purpose: reviewer role R4, checks Genie usability and cost.

Role: Usability and cost. Look for:
- Genie flows with too many steps, unclear wording, or questions it could answer itself
- token and context cost: files that load too much, tools that add overhead
- features not worth their complexity (propose cuts)
- places where a new user would get stuck or confused
Output: findings in hardening/findings.schema.md format. Prefer "remove" over "add". Do not edit anything.
