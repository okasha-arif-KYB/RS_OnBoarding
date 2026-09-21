from datetime import date, timedelta

from rest_framework import serializers

from .models import GPInst, InstanceRuleConfig, Rule


class GPInstSerializer(serializers.ModelSerializer):
    class Meta:
        model = GPInst
        fields = [
            "id",
            "entity",
            "name",
            "inst_id",
            "address",
            "recepient_address",
            "is_active_for_ltc",
            "is_active_outlook_notifications",
            "inst_order",
            "is_active",
            "created_at",
        ]


class RuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rule

        fields = [
            "key",
            "name",
            "description",
            "category",
            "rule_type",
            "display_order",
            "is_active",
            "field_schema",
        ]


class InstanceRuleConfigSerializer(serializers.ModelSerializer):
    rule_name = serializers.CharField(
        source="rule.name",
        read_only=True,
    )

    class Meta:
        model = InstanceRuleConfig

        fields = [
            "id",
            "instance",
            "rule",
            "rule_name",
            "is_enabled",
            "values",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "created_at",
            "updated_at",
        ]
        fields = [
            "id",
            "instance",
            "rule",
            "rule_name",
            "is_enabled",
            "system_type",
            "values",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "instance",   # comes from the URL, not the request body
            "created_at",
            "updated_at",
        ]

    def validate(self, attrs):
        """
        Validate and normalize rule configuration values.

        Existing doctorOrGroup mode normalization is preserved.

        Additionally, doctorOrGroup dateRangeEntries are expanded
        from:

            startDate -> endDate

        into individual daily entries.

        Example:

            2026-02-04 -> 2026-02-06

        becomes:

            2026-02-04
            2026-02-05
            2026-02-06
        """

        rule = attrs.get("rule") or getattr(
            self.instance,
            "rule",
            None,
        )

        values = attrs.get("values")

        if rule and values is not None:

            # Make sure values is actually an object/dictionary.
            if not isinstance(values, dict):
                raise serializers.ValidationError(
                    {
                        "values": (
                            "values must be a JSON object."
                        )
                    }
                )

            rule_key = getattr(
                rule,
                "key",
                str(rule),
            )

            # ---------------------------------------------------------
            # doctorOrGroup
            # ---------------------------------------------------------

            if rule_key == "doctorOrGroup":

                mode = values.get("mode")

                is_schedule = (
                    mode
                    in [
                        "schedule",
                        "combined",
                        "single_date",
                        "date_range",
                    ]
                    or (
                        bool(
                            values.get(
                                "singleDateEntries"
                            )
                        )
                        and mode != "fixed"
                    )
                    or (
                        bool(
                            values.get(
                                "dateRangeEntries"
                            )
                        )
                        and mode != "fixed"
                    )
                    or (
                        bool(
                            values.get("date")
                            or values.get("startDate")
                        )
                        and mode != "fixed"
                        and not values.get(
                            "defaultDoctor"
                        )
                    )
                )

                if is_schedule:

                    values.pop(
                        "defaultDoctor",
                        None,
                    )

                    values.pop(
                        "name",
                        None,
                    )

                    has_single = (
                        bool(
                            values.get(
                                "singleDateEntries"
                            )
                        )
                        or bool(
                            values.get("date")
                        )
                    )

                    has_range = (
                        bool(
                            values.get(
                                "dateRangeEntries"
                            )
                        )
                        or bool(
                            values.get("startDate")
                        )
                    )

                    if has_single and has_range:

                        values["mode"] = "combined"

                    elif has_single:

                        values["mode"] = "single_date"

                    elif has_range:

                        values["mode"] = "date_range"

                    else:

                        values["mode"] = "schedule"

                else:

                    values["mode"] = "fixed"

                    values.pop(
                        "singleDateEntries",
                        None,
                    )

                    values.pop(
                        "dateRangeEntries",
                        None,
                    )

                    values.pop(
                        "date",
                        None,
                    )

                    values.pop(
                        "startDate",
                        None,
                    )

                    values.pop(
                        "endDate",
                        None,
                    )

                # -----------------------------------------------------
                # NEW:
                # Expand dateRangeEntries
                # -----------------------------------------------------

                if values.get("dateRangeEntries"):

                    values[
                        "dateRangeEntries"
                    ] = self._expand_date_ranges(
                        values[
                            "dateRangeEntries"
                        ]
                    )

            # ---------------------------------------------------------
            # Existing field schema validation
            # ---------------------------------------------------------

            schema = rule.field_schema or {}

            if (
                schema.get("hasType")
                and "type" in values
            ):

                allowed = schema.get(
                    "typeOptions",
                    [],
                )

                if (
                    allowed
                    and values["type"]
                    not in allowed
                ):

                    raise serializers.ValidationError(
                        {
                            "values": (
                                f"'type' must be one of "
                                f"{allowed} for rule "
                                f"'{rule.key}'."
                            )
                        }
                    )

            if (
                schema.get("hasValue")
                and "value" in values
            ):

                if not isinstance(
                    values["value"],
                    (int, float),
                ):

                    raise serializers.ValidationError(
                        {
                            "values": (
                                f"'value' must be numeric "
                                f"for rule '{rule.key}'."
                            )
                        }
                    )

        return attrs

    def _expand_date_ranges(self, entries):
        """
        Convert every date range into individual daily entries.

        Input:

        {
            "id": "dr_1",
            "startDate": "2026-02-04",
            "endDate": "2026-02-06",
            "doctor": "Dr. Ali"
        }

        Output:

        [
            {
                "id": "dr_1_20260204",
                "date": "2026-02-04",
                "doctor": "Dr. Ali"
            },
            {
                "id": "dr_1_20260205",
                "date": "2026-02-05",
                "doctor": "Dr. Ali"
            },
            {
                "id": "dr_1_20260206",
                "date": "2026-02-06",
                "doctor": "Dr. Ali"
            }
        ]
        """

        if not isinstance(entries, list):

            raise serializers.ValidationError(
                {
                    "values": (
                        "dateRangeEntries must be a list."
                    )
                }
            )

        expanded_entries = []

        for index, entry in enumerate(entries):

            if not isinstance(entry, dict):

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "must be an object."
                        )
                    }
                )

            start_date_string = entry.get(
                "startDate"
            )

            end_date_string = entry.get(
                "endDate"
            )

            # If the entry is already a daily entry,
            # leave it alone.
            if (
                not start_date_string
                and not end_date_string
            ):

                if entry.get("date"):

                    expanded_entries.append(
                        entry
                    )

                    continue

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "must contain startDate "
                            "and endDate."
                        )
                    }
                )

            # Both dates are required for a range.
            if not start_date_string:

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "is missing startDate."
                        )
                    }
                )

            if not end_date_string:

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "is missing endDate."
                        )
                    }
                )

            # Parse dates.
            try:

                start_date = date.fromisoformat(
                    start_date_string
                )

            except (TypeError, ValueError):

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "has an invalid startDate. "
                            "Expected YYYY-MM-DD."
                        )
                    }
                )

            try:

                end_date = date.fromisoformat(
                    end_date_string
                )

            except (TypeError, ValueError):

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "has an invalid endDate. "
                            "Expected YYYY-MM-DD."
                        )
                    }
                )

            # End date cannot be before start date.
            if end_date < start_date:

                raise serializers.ValidationError(
                    {
                        "values": (
                            f"dateRangeEntries[{index}] "
                            "endDate cannot be before "
                            "startDate."
                        )
                    }
                )

            # Keep the doctor if it exists.
            doctor = entry.get("doctor")

            original_id = entry.get("id")

            current_date = start_date

            while current_date <= end_date:

                daily_entry = {
                    "id": (
                        f"{original_id}_"
                        f"{current_date.strftime('%Y%m%d')}"
                        if original_id
                        else (
                            f"dr_{current_date.strftime('%Y%m%d')}"
                        )
                    ),
                    "date": current_date.isoformat(),
                }

                # Don't force doctor if it wasn't supplied.
                if doctor is not None:

                    daily_entry["doctor"] = doctor

                expanded_entries.append(
                    daily_entry
                )

                current_date += timedelta(
                    days=1
                )

        return expanded_entries