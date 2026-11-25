from django.utils.timezone import now

from CRMUserAdmin.models import UserSession


class UpdateLastActivityMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            session_id = request.headers.get("Session-Id")

            if session_id:

                UserSession.objects.filter(session_id=session_id,is_logged_in=True
                ).update(last_activity=now())

        response = self.get_response(request)

        return response
    

#Step 6 — Frontend Send Session ID

# Store:

# localStorage.setItem(
#   "session_id",
#   response.data.session_id
# );

# Send in every API:

# headers: {
#    Authorization: `Bearer ${token}`,
#    "Session-Id": localStorage.getItem("session_id")
# }