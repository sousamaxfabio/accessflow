# AccessFlow RBAC Policy

## Purpose

AccessFlow calculates application access from an employee's approved role. Callers cannot directly choose application permissions.

## Policy principles

1. Grant only the access required by the role.
2. Deny access that is not explicitly listed.
3. Require human approval for sensitive permissions.
4. Keep policy decisions separate from account-provisioning actions.
5. Record the policy result in the audit history.

## Role policy matrix

| Role | Google Workspace | Slack | Notion | GitHub | Approval |
|---|---|---|---|---|---|
| Support Engineer | Standard user | Support channels | Support knowledge base: reader | No access | Not required |
| Automation Engineer | Standard user | Engineering and automation channels | Automation workspace: editor | Automation repositories: write | Required |
| Operations Manager | Standard user | Operations and incident channels | Operations workspace: editor | Operations repositories: read | Required |
| Finance Analyst | Standard user | Finance private channel | Finance workspace: reader | No access | Required |
| HR Specialist | Standard user | HR private channel | HR workspace: editor | No access | Required |

## Default-deny rule

If a role does not have a permission explicitly listed in this policy, AccessFlow must not grant it.

Unknown roles must be rejected rather than assigned approximate permissions.

## Approval rule

A policy result requires human approval when it includes sensitive data, private channels, write access to source code, or operational management access.

## Separation of responsibilities

The policy engine decides what access should be granted. Service adapters later simulate how that access would be applied to Slack, Notion, Google Workspace, and GitHub.