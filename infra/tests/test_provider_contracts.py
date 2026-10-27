"""Provider contracts. Copyright (C) 2026 Infosit d.o.o.; AGPL-3.0-or-later."""

import fnmatch
import json
import os
import secrets
import shutil
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
METADATA_ACTIONS = {
    "s3:ListBucket",
    "s3:GetBucketLocation",
    "s3:GetBucketPolicy",
    "s3:GetBucketAcl",
    "s3:GetBucketCORS",
    "s3:GetBucketWebsite",
    "s3:GetBucketVersioning",
    "s3:GetAccelerateConfiguration",
    "s3:GetBucketRequestPayment",
    "s3:GetBucketLogging",
    "s3:GetLifecycleConfiguration",
    "s3:GetReplicationConfiguration",
    "s3:GetEncryptionConfiguration",
    "s3:GetBucketObjectLockConfiguration",
    "s3:GetBucketTagging",
}


@pytest.mark.parametrize("location", ["fsn1", "nbg1"])
def test_actual_provider_checks_returned_volume_location(tmp_path, location):
    root = tmp_path / "node"
    shutil.copytree(ROOT / "infra/node", root, ignore=shutil.ignore_patterns(".terraform"))
    (root / ".terraform").symlink_to(ROOT / "infra/node/.terraform", target_is_directory=True)
    response = {
        "volume": {
            "id": 123456,
            "name": "example-dev-postgres",
            "created": "2026-10-26T00:00:00Z",
            "size": 20,
            "server": None,
            "linux_device": "/dev/disk/by-id/scsi-0HC_Volume_123456",
            "labels": {"tenant": "example", "environment": "dev"},
            "protection": {"delete": True},
            "status": "available",
            "format": "",
            "location": {
                "id": 2,
                "name": location,
                "description": "Documentation-only German location",
                "country": "DE",
                "city": "Nuremberg",
                "latitude": 49.45,
                "longitude": 11.08,
                "network_zone": "eu-central",
            },
        }
    }
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append(self.path)
            if self.path != "/v1/volumes/123456":
                self.send_error(404)
                return
            body = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    expected_failures = "[hcloud_server.node]" if location != "fsn1" else "[]"
    (root / "tests/location.tftest.hcl").write_text(
        f"""
provider "hcloud" {{
  endpoint = "http://127.0.0.1:{server.server_port}/v1"
}}
run "returned_volume_location" {{
  command = plan
  expect_failures = {expected_failures}
  assert {{
    condition = data.hcloud_volume.postgres.location == "{location}"
    error_message = "Check the provider's returned location, not the lookup selector."
  }}
}}
"""
    )
    try:
        result = subprocess.run(
            [
                "terraform",
                f"-chdir={root}",
                "test",
                "-filter=tests/location.tftest.hcl",
                "-var-file=examples/dev.tfvars",
                "-no-color",
            ],
            env=dict(os.environ, HCLOUD_TOKEN=secrets.token_hex(32)),
            capture_output=True,
            text=True,
            timeout=120,
        )
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
    assert requests == ["/v1/volumes/123456"]
    assert result.returncode == 0, result.stdout + result.stderr


def matches(value, patterns):
    if isinstance(patterns, str):
        patterns = [patterns]
    return any(fnmatch.fnmatchcase(value, pattern) for pattern in patterns)


def allows(policy, principal, action, resource, inherited=False):
    allowed = inherited
    for statement in policy["Statement"]:
        if "Principal" in statement and not matches(principal, statement["Principal"]["AWS"]):
            continue
        if "NotPrincipal" in statement and matches(principal, statement["NotPrincipal"]["AWS"]):
            continue
        if not matches(action, statement["Action"]):
            continue
        if "Resource" in statement and not matches(resource, statement["Resource"]):
            continue
        if "NotResource" in statement and matches(resource, statement["NotResource"]):
            continue
        assert "Condition" not in statement
        if statement["Effect"] == "Deny":
            return False
        allowed = True
    return allowed


@pytest.mark.parametrize("environment", ["dev", "prod"])
def test_retained_plan_key_reads_metadata_but_cannot_access_or_mutate_data(environment):
    result = subprocess.run(
        [
            "terraform",
            f"-chdir={ROOT / 'infra/retained'}",
            "test",
            "-json",
            "-verbose",
            f"-var-file=examples/{environment}.tfvars",
        ],
        capture_output=True,
        text=True,
        check=True,
        timeout=120,
    )
    plan = next(
        record["test_plan"]
        for line in result.stdout.splitlines()
        if (record := json.loads(line)).get("type") == "test_plan"
    )
    policy = json.loads(
        next(
            resource["change"]["after"]["policy"]
            for resource in plan["resource_changes"]
            if resource["address"] == "aws_s3_bucket_policy.backup"
        )
    )
    project = "123" if environment == "dev" else "223"
    principal = f"arn:aws:iam:::user/p{project}459:PLANEXAMPLE"
    node = f"arn:aws:iam:::user/p{project}456:NODEEXAMPLE"
    bucket = f"arn:aws:s3:::example-{environment}-backup-documentation"
    own_object = f"{bucket}/example/{environment}/epoch-1/backup"
    foreign_object = f"{bucket}/other-tenant/{environment}/epoch-1/backup"
    grants = [
        statement
        for statement in policy["Statement"]
        if statement["Effect"] == "Allow" and statement.get("Principal", {}).get("AWS") == principal
    ]
    assert len(grants) == 1
    assert set(grants[0]["Action"]) == METADATA_ACTIONS
    assert grants[0]["Resource"] == bucket
    for action in METADATA_ACTIONS:
        assert allows(policy, principal, action, bucket), action
        assert not allows(policy, principal, action, "arn:aws:s3:::other-tenant-backup"), action
    for action in (
        "s3:GetObject",
        "s3:GetObjectVersion",
        "s3:PutObject",
        "s3:DeleteObject",
        "s3:DeleteObjectVersion",
        "s3:PutObjectAcl",
        "s3:AbortMultipartUpload",
        "s3:RestoreObject",
    ):
        for resource in (own_object, foreign_object):
            assert not allows(policy, principal, action, resource, inherited=True), action
    for action in (
        "s3:PutBucketPolicy",
        "s3:DeleteBucketPolicy",
        "s3:PutBucketAcl",
        "s3:PutLifecycleConfiguration",
        "s3:PutBucketVersioning",
        "s3:CreateBucket",
        "s3:DeleteBucket",
    ):
        assert not allows(policy, principal, action, bucket, inherited=True), action
    assert allows(policy, node, "s3:GetObject", own_object)
    assert allows(policy, node, "s3:PutObject", own_object)
    assert not allows(policy, node, "s3:DeleteObject", own_object, inherited=True)
    assert not allows(policy, node, "s3:PutBucketPolicy", bucket, inherited=True)
    assert not allows(policy, node, "s3:GetObject", foreign_object, inherited=True)
