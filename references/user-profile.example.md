# Local User Profile Example

Copy this file to `user-profile.md` in the same directory, fill only the rules the user explicitly requested, and keep that local file untracked. Never infer a preference from this example.

## Address rule

- Preferred name: `PREFERRED_NAME`
- Require the exact preferred name in every user-facing message: `yes` or `no`
- Before each message, check the draft against this rule.

## Recovery after a mandatory communication-rule miss

- Stop substantive work: `yes` or `no`
- Maximum automatic replacement tasks per active request: `NUMBER`
- If replacement is required, use the host's native task or conversation capability.
- Sanitize the handoff. Include only the active goal, decisions, verified state, completed changes and checks, blockers, next action, and applicable preferences.
- Open the replacement task when the host permits it. Leave the prior task unarchived unless the user requests otherwise.
- If replacement creation or navigation fails, report the failure without claiming a restart occurred.

## Other local rules

Add only explicit user preferences that need to apply whenever this skill runs. Do not put credentials, tokens, secrets, private records, or unrelated personal information in this file.
