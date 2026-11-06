# purpose: Gherkin skeleton for behaviour tests; business language only, tags carry REQ ID and tier.
@regression @tier1 @REQ-AREA-001
Feature: <business capability>

  Scenario: <one behaviour with concrete values>
    Given <state set up through an API or data builder, not the UI>
    When <one business action>
    Then <observable result>
