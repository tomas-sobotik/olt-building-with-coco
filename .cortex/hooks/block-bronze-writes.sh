#!/bin/bash
INPUT=$(cat)
SQL=$(echo "$INPUT" | jq -r '.tool_input.sql // empty')

if echo "$SQL" | grep -iq 'BRONZE' && echo "$SQL" | grep -iqE '^[[:space:]]*(ALTER|DROP|INSERT|UPDATE|DELETE|MERGE|CREATE|TRUNCATE)'; then
  echo "BRONZE schema is immutable — modifications are not allowed." >&2
  exit 2
fi
