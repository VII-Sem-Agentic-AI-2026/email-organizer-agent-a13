from lab1_agent import EmailOrganizerAgent, EmailRequest


def sample_details():
    return EmailRequest(
        request="Organize faculty emails",
        folders=["inbox"],
        priority_rules=["deadlines", "urgent requests"],
        output_format="triaged inbox with draft replies"
    )


def test_vague_request_clarifies_three_details():
    answers = iter(["inbox, faculty", "deadlines, urgent", "triaged inbox"])
    agent = EmailOrganizerAgent()
    details = agent.clarify("Organize my emails", lambda _: next(answers))
    assert details.folders == ["inbox", "faculty"]
    assert len(details.priority_rules) == 2
    assert details.output_format == "triaged inbox"


def test_plan_contains_required_workflow():
    plan = EmailOrganizerAgent().create_plan(sample_details())
    assert len(plan.steps) >= 7
    assert any("Rank emails" in step for step in plan.steps)
    assert any("reply drafts" in step for step in plan.steps)


def test_add_step_revision():
    agent = EmailOrganizerAgent()
    plan = agent.create_plan(sample_details())
    old_count = len(plan.steps)
    agent.revise(plan, "add step: Group student queries")
    assert len(plan.steps) == old_count + 1
    assert plan.steps[-1] == "Group student queries"


def test_replace_step_revision():
    agent = EmailOrganizerAgent()
    plan = agent.create_plan(sample_details())
    agent.revise(plan, "replace step 1 with Read inbox and archive folders")
    assert plan.steps[0] == "Read inbox and archive folders"


def test_remove_step_revision():
    agent = EmailOrganizerAgent()
    plan = agent.create_plan(sample_details())
    old_count = len(plan.steps)
    agent.revise(plan, "remove step 5")
    assert len(plan.steps) == old_count - 1


def test_goal_revision():
    agent = EmailOrganizerAgent()
    plan = agent.create_plan(sample_details())
    agent.revise(plan, "change goal: Prepare weekly inbox report")
    assert plan.goal == "Prepare weekly inbox report"


def test_blank_feedback_keeps_plan_unchanged():
    agent = EmailOrganizerAgent()
    plan = agent.create_plan(sample_details())
    old_steps = plan.steps.copy()
    agent.revise(plan, "")
    assert plan.steps == old_steps
