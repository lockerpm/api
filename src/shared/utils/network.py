from user_agents import parse


def detect_device(request):
    """
    Detect device information from request
    :param request:
    :return:
    """
    ua_string = request.META.get("HTTP_USER_AGENT")
    if not ua_string:
        return {}

    device_information = dict()
    user_agent = parse(ua_string)
    # Accessing user agent to retrieve browser attributes
    device_information["browser"] = {
        "family": user_agent.browser.family,
        "version": user_agent.browser.version_string
    }

    # Accessing user agent to retrieve operating system properties
    device_information["os"] = {
        "family": user_agent.os.family,
        "version": user_agent.os.version_string
    }

    # Accessing user agent to retrieve device properties
    device_information["device"] = {
        "family": user_agent.device.family,
        "brand": user_agent.device.brand,
        "model": user_agent.device.model,
        "is_mobile": user_agent.is_mobile,
        "is_tablet": user_agent.is_tablet,
        "is_pc": user_agent.is_pc,
        "is_bot": user_agent.is_bot
    }
    return device_information
