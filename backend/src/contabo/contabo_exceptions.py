class ContaboAuthError(Exception):
    """Custom exception for Contabo authentication errors"""
    pass


class ContaboInstanceCreationError(Exception):
    """Custom exception for Contabo instance creation errors"""
    pass


class InstanceSetupError(Exception):
    """Custom exception for instance setup errors"""
    pass


class SetupInstanceError(Exception):
    """Custom exception for setup instance errors"""
    pass


class InstanceStatusCheckError(Exception):
    """Custom exception for instance status check errors"""
    pass


class InstanceCancellationError(Exception):
    """Custom exception for instance cancellation errors"""
    pass


class BatchProcessError(Exception):
    """Custom exception for batch process errors"""
    pass
