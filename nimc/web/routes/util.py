from fastapi.responses import HTMLResponse


def success(message: str) -> HTMLResponse:
    """Helper function to create a success HTML response"""
    return HTMLResponse(
        content=f'<span class="success-message">{message}</span>',
        status_code=200,
    )


def error(message: str) -> HTMLResponse:
    """Helper function to create an error HTML response"""
    return HTMLResponse(
        content=f'<span class="error-message">{message}</span>',
        status_code=200,
    )
