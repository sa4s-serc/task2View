# Why this view looks like this
- **Level rule:** perspective "one feature" → *balanced* (SKILL.md §1.2); budget ≤ 7 lifelines / ≤ 12 messages, used 4 lifelines / 7 messages.
- **Lifelines are roles:** client, web controller, repository, database. DispatcherServlet, WebDataBinder, Bean Validation and Hibernate are collapsed into the controller and repository (§3); validation is one self-message.
- **One `alt`:** success vs. field errors, the path the tester asked for (§3 "one alt for the error path"). The error reply lists what the tests assert (OwnerControllerTests.java:125-134): blank, too long, telephone not 10 digits.
- **Left out:** the GET that shows the empty form, the follow-up GET after the redirect, and DB failures (not handled in this method).
- **Wording:** engineering audience → HTTP status codes and view names on replies.
- **Inventory:** the validation self-message has no element of its own; its evidence (Owner/Person constraints) is on the controller lifeline.
- **Checks:** puml-check OK (one `info`: the else label sits on the first lifeline, as PlantUML draws it); check_inventory 0 issues.
