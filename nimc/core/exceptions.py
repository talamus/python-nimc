class AdHocError(Exception):
    """Base exception for the nimc module."""


class MissingResource(AdHocError):
    """Raised when a requested resource is not found."""

    def __init__(
        self, resource_type: str, identifier: int | str, help: str | None = None
    ) -> None:
        """
        Raised when a requested resource is not found.

        :param self: Exception being created
        :param resource_type: Description of the resource type (e.g., "server", "firewall")
        :param identifier: The name or ID of the missing resource
        :param help: Optional help message providing additional context or instructions for resolving the issue.
                     If not provided, a default message will be generated.
        """
        self.resource_type = resource_type
        self.identifier = identifier
        self.help = help or (
            "Please verify the name or ID and check that it exists in the "
            "Hetzner Cloud Console (https://console.hetzner.com)."
        )
        super().__init__(
            f"The {self.resource_type} '{self.identifier}' could not be found."
        )
