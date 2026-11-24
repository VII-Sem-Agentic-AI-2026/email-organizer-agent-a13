import nbformat

nb = nbformat.v4.new_notebook()
nb.cells = [
    nbformat.v4.new_markdown_cell(
        "# Lab 1 — Agent vs Chatbot\n"
        "## Email Organizer Agent\n"
        "This notebook demonstrates clarification, planning, observation and revision. "
        "It does not access Gmail or send emails."
    ),
    nbformat.v4.new_code_cell(
        "from lab1_agent import EmailOrganizerAgent\n"
        "agent = EmailOrganizerAgent()"
    ),
    nbformat.v4.new_markdown_cell(
        "## 1. User request and clarification\n"
        "Enter a vague request. The agent asks three clarification questions."
    ),
    nbformat.v4.new_code_cell(
        "request = input('Describe your email-organizing request: ').strip()\n"
        "while not request:\n"
        "    request = input('Please enter a request: ').strip()\n"
        "details = agent.clarify(request)"
    ),
    nbformat.v4.new_markdown_cell("## 2. Generate the editable plan"),
    nbformat.v4.new_code_cell(
        "plan = agent.create_plan(details)\n"
        "plan.display()"
    ),
    nbformat.v4.new_markdown_cell(
        "## 3. Observe feedback and revise\n"
        "Examples: `add step: Group student queries separately`, "
        "`replace step 4 with Extract only confirmed deadlines`, "
        "`remove step 5`, or `change goal: Prepare a weekly faculty inbox report`."
    ),
    nbformat.v4.new_code_cell(
        "while True:\n"
        "    feedback = input('Feedback (Enter to accept): ').strip()\n"
        "    if not feedback:\n"
        "        break\n"
        "    try:\n"
        "        agent.revise(plan, feedback)\n"
        "        plan.display()\n"
        "    except ValueError as error:\n"
        "        print(error)"
    ),
    nbformat.v4.new_markdown_cell("## 4. Final plan"),
    nbformat.v4.new_code_cell(
        "plan.display()\n"
        "print('\\nNotebook demonstration completed. No email was sent.')"
    )
]
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3"
    }
}
nbformat.validate(nb)
nbformat.write(nb, "Lab1_Email_Organizer.ipynb")
print("Notebook created and validated.")
