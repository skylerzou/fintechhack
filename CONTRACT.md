##CONTRACT.MD
        #not a perfect source of truth
##CONVENTIONS:
{% for r in requests %}
{{ user.get_full_name|default:user.username }}

# BASE.HTML
    # How to Make a New Page

    Every page on the site shares the same header, footer, and styling.
    You only write the parts that are different on your page.

    ## Start by copying this

    ```html
    {% extends "base.html" %}
    {% load static %}

    {% block title %}Your Page Name{% endblock %}

    {% block content %}
    <!-- Your page content goes here -->
    {% endblock %}
    ```

    Don't change the first line. `{% load static %}` must stay on line 2 if you
    use `{% static %}` anywhere in your page (images, your own CSS or JS files).


    ## The 4 sections you can fill in

    | Section | What it controls | Required? |
    |---|---|---|
    | `title` | The text on the browser tab (the site name is added automatically) | **Yes** |
    | `content` | Everything visible on the page | **Yes** |
    | `extra_head` | Styling used only on your page | No |
    | `extra_js` | Interactive behavior used only on your page | No |

    Shared styling and scripts load automatically. `extra_head` and `extra_js`
    only add to them, so there is nothing to preserve.

    ## Available on every page

    | Name | What it is |
    |---|---|
    | `user` | The logged-in user. Use `{{ user.get_full_name\|default:user.username }}` |
    | `current_org` | The organization in the URL, or `None` on pages with no org (login, etc.) |
    | `messages` | Flash messages to show the user |
    The base header should have a logout button, so child pages dont need one,

    **`current_org` is empty outside an org.** If your page can render without an
    org, wrap org-specific parts in `{% if current_org %}...{% endif %}`.

    ## Rules

    1. Never edit `base.html`. (at least after its finalized)
    2. Every page needs a `title` and `content`. If you forget `title`, the tab shows only the site name.
    3. Only write inside the `{% block %}` ... `{% endblock %}` lines. Anything outside them is ignored, except {% extends %} and {% load %}
    4. Logout must be a POST form, never a plain link
    5. wrap user-specific parts in {% if user.is_authenticated %} no anon users

    ```html
    <form method="post" action="{% url 'logout' %}">
    {% csrf_token %}
    <button type="submit">Log out</button>
    </form>
    ```

    ---


    ## base.html requirement

    Put shared CSS and JS outside the overridable blocks, and leave the blocks empty:

    ```html
    <head>
    <title>{% block title %}{% endblock %} | Site Name</title>
    <link rel="stylesheet" href="{% static 'css/site.css' %}">
    {% block extra_head %}{% endblock %}
    </head>
    ...
    <script src="{% static 'js/site.js' %}"></script>
    {% block extra_js %}{% endblock %}
    ```

    A page can't break the shared assets because they aren't inside a block.
    This is why page authors don't need `{{ block.super }}`.

## Request flow

    URL: `/orgs/acme/requests/42/accept/`

    1. Middleware (`process_view`): slug "acme" → Organization, verify membership → `request.org`
    2. View: passes `request.org` to the service
    3. Service: `.get(pk=..., organization=org)`, then `required_role(...)`
    4. Context processor: exposes `request.org` as `current_org`
    5. `base.html`: header and nav links use `current_org`

    ## Traps

    - **Use `process_view`, not `__call__`.** `__call__` runs before URL matching, so the slug isn't available yet. `process_view` runs after matching and receives the URL kwargs.
    - **Views still receive the slug.** Every org view's signature must accept `org_slug`, or Django raises `TypeError`.
    - **Pages without an org.** Middleware must do nothing when there's no slug (login, admin). The context processor must set `current_org = None` and never assume `request.org` exists.

    ## Expected behavior

    | Request | Result |
    |---|---|
    | Member of acme → `/orgs/acme/requests/42/accept/` | `request.org = acme`, service runs |
    | Non-member → same URL | 404 from middleware |
    | Anyone → `/orgs/doesnotexist/...` | 404 |
    | Anyone → `/login/` | Middleware skips; `current_org = None`; `base.html` renders |
## View Requests (Treasurer)

- Template: `finance/request_list.html`
- URL name: `request-list` → `/finance/requests/`
- Access: logged-in AND treasurer role only (everyone else gets a 403 page)
- Extends: `base.html`, fills `{% block content %}`

    ## Context
    | Variable | Type | Notes |
    |---|---|---|
    | `SpendingReq` | queryset of SpendingReq | newest first, may be empty |
    | `SpendingReq[].id` | int | for building links only, never display |
    | `SpendingReq[].requestedby` | User |  first name last name|

    | `SpendingReq[].completedby` | User | can be null |
    | `SpendingReq[].acceptedby` | User | can be null|

    | `SpendingReq[].title` | str | |
    | `SpendingReq[].spend` | Decimal | display as `{{ r.spend\|floatformat:2 }}` with a `$` before it |
    | `SpendingReq[].reimamount` | Decimal | display as `{{ r.reimamount\|floatformat:2 }}` with a `$` before it | can be null show "-" no $
    | `SpendingReq[].status` | str | exactly one of `PENDING`, `APPROVED`, `DENIED` , `SUBMITTED`, `COMPLETED`|
    | `SpendingReq[].created_at` | datetime | 
    | `status_filter` | str | currently selected filter: `all`, `PENDING`, `APPROVED`, `DENIED`, `SUBMITTED`, `COMPLETED`|
    | `pending_count` | int | for the badge next to the page title |

    Forms
    **Filter**: GET to `request-list`, one field: `status` (select; values `all`, `PENDING`, `APPROVED`, `DENIED`, `SUBMITTED`, `COMPLETED`). Preselect `status_filter`.

    **Approve** (one per pending row): POST to `{% url 'request-approve' r.id %}`, include `{% csrf_token %}`, no other fields. Only render for rows where `status == "PENDING"`.

    **Deny**: same as Approve but to `{% url 'request-deny' r.id %}`.

    **COMPLETE**:  (one per pending row): POST to `{% url 'request-complete' r.id %}`, include `{% csrf_token %}`, no other fields. Only render for rows where `status == "SUBMITTED"`.

    ### Links
    - Each row's title links to `{% url 'request-detail' r.id %}`
    - Page header has a "Back to dashboard" link to `{% url 'dashboard' %}`

    ### States
    - Empty: show "No requests match this filter."
    - Status shown as a colored label (pending = yellow, approved = green, denied = red, submitted =  orange, completed = blue), with the status text always visible too, not color alone
    - After approve/deny, the backend redirects back here with a flash message; display Django `messages` at the top (the base template already does this)

    ### Do NOT
    - Compute totals or counts in the template (use the variables above)
    - Hardcode any URL paths
    - Invent fields not listed above (if you need one, ask the backend person)
    - Add JavaScript fetch calls (approve/deny are plain form posts)


