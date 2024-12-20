class VPSConnectionError(Exception):
    """Custom exception for VPS connection errors"""
    pass


class VPSAuthenticationError(Exception):
    """Custom exception for VPS authentication errors"""
    pass


class VPSFileOperationError(Exception):
    """Custom exception for VPS file operation errors"""
    pass


class VPSSetupError(Exception):
    """Custom exception for VPS setup errors"""
    pass


class VPSExecutionError(Exception):
    """Custom exception for VPS script execution errors"""
    pass


class VPSPrivilegeElevationError(Exception):
    """Custom exception for VPS script execution errors"""
    pass


class VPSFileUploadError(Exception):
    """Custom exception for VPS script execution errors"""
    pass
