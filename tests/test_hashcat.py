import json
from unittest.mock import patch, MagicMock
from hashcat_bench.hashcat import fetch_tags, fetch_releases, fetch_branch_head, latest_stable


def _mock_urlopen(data):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(data).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


@patch("hashcat_bench.hashcat.urlopen")
def test_fetch_tags(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen([
        {"name": "v6.2.6"},
        {"name": "v6.2.5"},
        {"name": "v6.2.4"},
        {"name": "master"},
    ])
    tags = fetch_tags()
    assert tags == ["v6.2.6", "v6.2.5", "v6.2.4"]
    assert "master" not in tags


@patch("hashcat_bench.hashcat.urlopen")
def test_fetch_releases(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen([
        {"tag_name": "v6.2.6", "published_at": "2022-09-02T10:00:00Z", "prerelease": False},
        {"tag_name": "v6.2.5", "published_at": "2021-11-21T10:00:00Z", "prerelease": False},
        {"tag_name": "v6.2.6-rc1", "published_at": "2022-08-20T10:00:00Z", "prerelease": True},
    ])
    releases = fetch_releases()
    assert len(releases) == 2
    assert releases[0]["version"] == "v6.2.6"
    assert releases[0]["date"] == "2022-09-02"
    assert releases[1]["version"] == "v6.2.5"


@patch("hashcat_bench.hashcat.urlopen")
def test_latest_stable(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen([
        {"tag_name": "v6.2.6", "published_at": "2022-09-02T10:00:00Z", "prerelease": False},
        {"tag_name": "v6.2.5", "published_at": "2021-11-21T10:00:00Z", "prerelease": False},
    ])
    assert latest_stable() == "v6.2.6"


@patch("hashcat_bench.hashcat.urlopen")
def test_latest_stable_skips_prereleases(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen([
        {"tag_name": "v6.2.7-rc1", "published_at": "2023-01-01T10:00:00Z", "prerelease": True},
        {"tag_name": "v6.2.6", "published_at": "2022-09-02T10:00:00Z", "prerelease": False},
    ])
    assert latest_stable() == "v6.2.6"


@patch("hashcat_bench.hashcat.urlopen")
def test_fetch_branch_head(mock_urlopen):
    mock_urlopen.return_value = _mock_urlopen({
        "sha": "abc12345def67890",
        "commit": {
            "committer": {"date": "2026-04-20T15:30:00Z"},
            "message": "Fix buffer overflow in OpenCL kernel\n\nDetails here",
        },
    })
    head = fetch_branch_head("master")
    assert head["branch"] == "master"
    assert head["sha"] == "abc12345"
    assert head["date"] == "2026-04-20"
    assert "Fix buffer overflow" in head["message"]
    assert "\n" not in head["message"]
