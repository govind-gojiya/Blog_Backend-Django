from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to allow owners of an object to edit and delete it.
    """

    def has_object_permission(self, request, view, obj):
        """
        Returns True if the request is a safe method (GET, OPTIONS, HEAD) or if the
        requesting user is the owner of the post.
        """

        # Allow safe methods (GET, OPTIONS, HEAD)
        if request.method in SAFE_METHODS:
            return True

        # Check if the user is authenticated and the owner of the post
        return obj.owner == request.user