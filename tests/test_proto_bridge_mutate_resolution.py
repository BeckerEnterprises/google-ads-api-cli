"""Reflection tests against real generated GAPIC/protobuf classes (no network)."""

from __future__ import annotations

import pytest

from googleadscli import proto_bridge as pb


@pytest.mark.parametrize(
    "resource_key, expected_method",
    [
        ("campaign", "mutate_campaigns"),
        ("campaign_budget", "mutate_campaign_budgets"),
        ("ad_group", "mutate_ad_groups"),
        # Irregular pluralization: criterion -> criteria.
        ("ad_group_criterion", "mutate_ad_group_criteria"),
        ("ad_group_ad", "mutate_ad_group_ads"),
        ("customer_label", "mutate_customer_labels"),
    ],
)
def test_resolve_mutate_target_finds_correct_method(fake_client, resource_key, expected_method):
    target = pb.resolve_mutate_target(fake_client, resource_key, version="v25")
    assert target.method_name == expected_method
    assert target.operation_cls.__name__ == f"{pb.to_camel(resource_key)}Operation"


def test_resolve_mutate_target_unknown_resource_raises(fake_client):
    with pytest.raises(pb.BridgeError):
        pb.resolve_mutate_target(fake_client, "not_a_real_resource", version="v25")


def test_build_operation_create(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    op = pb.build_operation(
        target,
        {"create": {"name": "Test Campaign", "status": "PAUSED", "advertising_channel_type": "SEARCH"}},
    )
    assert op.create.name == "Test Campaign"
    assert op.create.status.name == "PAUSED"


def test_build_operation_update_auto_derives_field_mask(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    op = pb.build_operation(
        target,
        {"update": {"resource_name": "customers/123/campaigns/999", "status": "ENABLED"}},
    )
    assert set(op.update_mask.paths) == {"resource_name", "status"}


def test_build_operation_update_explicit_field_mask(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    op = pb.build_operation(
        target,
        {
            "update": {"resource_name": "customers/123/campaigns/999", "status": "ENABLED"},
            "update_mask": ["status"],
        },
    )
    assert list(op.update_mask.paths) == ["status"]


def test_build_operation_update_without_resource_name_raises(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    with pytest.raises(pb.BridgeError):
        pb.build_operation(target, {"update": {"status": "ENABLED"}})


def test_build_operation_remove(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    op = pb.build_operation(target, {"remove": "customers/123/campaigns/999"})
    assert op.remove == "customers/123/campaigns/999"


def test_build_operation_requires_exactly_one_key(fake_client):
    target = pb.resolve_mutate_target(fake_client, "campaign", version="v25")
    with pytest.raises(pb.BridgeError):
        pb.build_operation(target, {})
    with pytest.raises(pb.BridgeError):
        pb.build_operation(target, {"create": {}, "remove": "x"})
