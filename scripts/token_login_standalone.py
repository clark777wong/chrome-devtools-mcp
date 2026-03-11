# -*- coding: utf-8 -*-
"""
Token 登录脚本 - 独立版本
=====================================
可直接复制到其他项目使用

功能:
- 使用 Token 注入实现自动登录
- 支持环境变量、.env 文件、配置文件或参数传入
- 支持登录状态验证

使用方法:
    # 方式1: 使用环境变量（推荐，最安全）
    $env:AUTH_TOKEN = "your_token"
    python token_login_standalone.py
    
    # 方式2: 使用 .env 文件（推荐用于项目集成）
    # 创建 .env 文件: AUTH_TOKEN=your_token
    python token_login_standalone.py
    
    # 方式3: 作为模块导入
    from token_login_standalone import TokenLogin, login_with_token
    
    login = TokenLogin(token="your_token", user_info={"username": "xxx"})
    login.inject_to_page(page, "https://example.com")

依赖: pip install playwright python-dotenv
"""

import json
import os
import logging
from pathlib import Path
from typing import Tuple, Optional
from dataclasses import dataclass

from playwright.sync_api import Page

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

logger = logging.getLogger(__name__)

ENV_FILE = Path(__file__).parent / ".env"
if DOTENV_AVAILABLE and ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DEFAULT_CONFIG = {
    "base_url": "",
    "expected_username": "",
    "token_key": "token",
    "user_info_key": "user_info",
    "expires_at": ""
}

CONFIG_FILE = Path(__file__).parent / "token_config.json"


@dataclass
class AuthData:
    """认证数据"""
    token: str
    user_info: dict
    expires_at: Optional[str] = None


class TokenLogin:
    """
    Token 登录器
    
    Example:
        >>> login = TokenLogin(
        ...     token="eyJhbGci...",
        ...     user_info={"username": "User", "id": 123}
        ... )
        >>> login.inject_to_page(page, "https://example.com")
        >>> is_success, error = login.verify_login(page, "User")
    """
    
    def __init__(self, token: str, user_info: dict, expires_at: str = None):
        self.token = token
        self.user_info = user_info
        self.expires_at = expires_at
    
    def inject_to_page(self, page: Page, base_url: str) -> None:
        current_url = page.url
        if not current_url or "about:blank" in current_url:
            page.goto(base_url)
            page.wait_for_load_state("domcontentloaded")
        
        user_info_json = json.dumps(self.user_info, ensure_ascii=False)
        expires_at = self.expires_at or ""
        
        page.evaluate(f"""() => {{
            localStorage.setItem('token', {json.dumps(json.dumps(self.token))});
            localStorage.setItem('user_info', {json.dumps(user_info_json)});
            localStorage.setItem('expires_at', {json.dumps(expires_at)});
            
            document.cookie = 'token=' + encodeURIComponent({json.dumps(self.token)}) + '; path=/';
            document.cookie = 'user_info=' + encodeURIComponent({json.dumps(user_info_json)}) + '; path=/';
            document.cookie = 'expires_at=' + encodeURIComponent({json.dumps(expires_at)}) + '; path=/';
        }}""")
        
        page.reload()
        page.wait_for_load_state("networkidle")
    
    def verify_login(self, page: Page, expected_username: str = None, timeout: int = 5000) -> Tuple[bool, str]:
        if expected_username is None:
            expected_username = self.user_info.get("username", "")
        
        login_btn = page.locator("text=登录").or_(
            page.locator("text=注册")
        ).or_(
            page.locator("text=登录/注册")
        )
        
        try:
            login_button_visible = login_btn.first.is_visible(timeout=timeout)
        except Exception:
            login_button_visible = False
        
        username_locator = page.locator(f"text={expected_username}")
        try:
            username_visible = username_locator.first.is_visible(timeout=timeout)
        except Exception:
            username_visible = False
        
        is_logged_in = (not login_button_visible) and username_visible
        
        error_msg = ""
        if not is_logged_in:
            error_parts = []
            if login_button_visible:
                error_parts.append("仍显示'登录/注册'按钮")
            if not username_visible:
                error_parts.append(f"未检测到用户 '{expected_username}'")
            error_msg = "登录状态校验失败: " + " 且 ".join(error_parts)
        
        return is_logged_in, error_msg


def load_config() -> dict:
    """加载配置文件"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """保存配置文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_auth_data() -> AuthData:
    """
    获取认证数据
    
    优先级: 环境变量 > .env 文件 > 配置文件
    """
    config = load_config()
    
    token = os.getenv("AUTH_TOKEN") or config.get("token")
    user_info_str = os.getenv("AUTH_USER_INFO")
    if user_info_str:
        try:
            user_info = json.loads(user_info_str)
        except json.JSONDecodeError:
            user_info = {"username": user_info_str}
    else:
        user_info = config.get("user_info", {})
    
    expires_at = os.getenv("AUTH_EXPIRES_AT") or config.get("expires_at")
    
    if not token:
        raise ValueError(
            "Token 未配置。请通过以下方式之一配置:\n"
            "  1. 环境变量: $env:AUTH_TOKEN = 'your_token'\n"
            "  2. .env 文件: AUTH_TOKEN=your_token\n"
            "  3. 配置文件: token_config.json 中的 token 字段"
        )
    
    return AuthData(token=token, user_info=user_info, expires_at=expires_at)


def login_with_token(
    page: Page,
    token: str = None,
    user_info: dict = None,
    base_url: str = None,
    expected_username: str = None
) -> Tuple[bool, str]:
    """
    一键登录函数
    
    Args:
        page: Playwright 页面对象
        token: Token 字符串（不传则从配置获取）
        user_info: 用户信息（不传则从配置获取）
        base_url: 目标 URL（不传则从配置获取）
        expected_username: 期望用户名（用于验证）
        
    Returns:
        Tuple[bool, str]: (是否成功, 错误信息)
    """
    config = load_config()
    
    if token is None:
        token = os.getenv("AUTH_TOKEN") or config.get("token")
    
    if user_info is None:
        user_info = config.get("user_info", {})
    
    if base_url is None:
        base_url = config.get("base_url", DEFAULT_CONFIG["base_url"])
    
    if not token:
        return False, "Token 未配置"
    
    login = TokenLogin(token, user_info)
    login.inject_to_page(page, base_url)
    
    return login.verify_login(page, expected_username)


def main():
    """独立运行 - 测试登录"""
    from playwright.sync_api import sync_playwright
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("=" * 60)
    print("Token 登录脚本 - 独立运行模式")
    print("=" * 60)
    
    try:
        auth_data = get_auth_data()
        logger.info(f"Token 已加载 (长度: {len(auth_data.token)} 字符)")
        logger.info(f"用户: {auth_data.user_info.get('username', 'N/A')}")
    except ValueError as e:
        logger.error(f"{e}")
        print("\n请创建 token_config.json 配置文件，格式如下:")
        print(json.dumps({
            "token": "your_jwt_token_here",
            "user_info": {"username": "Your Name", "id": 123},
            "base_url": "https://your-site.com",
            "expires_at": "2026-12-31T23:59:59"
        }, ensure_ascii=False, indent=2))
        return
    
    config = load_config()
    base_url = config.get("base_url", DEFAULT_CONFIG["base_url"])
    expected_username = auth_data.user_info.get("username", DEFAULT_CONFIG["expected_username"])
    
    logger.info(f"目标 URL: {base_url}")
    logger.info(f"期望用户: {expected_username}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()
        
        logger.info("执行登录...")
        is_success, error_msg = login_with_token(
            page,
            token=auth_data.token,
            user_info=auth_data.user_info,
            base_url=base_url,
            expected_username=expected_username
        )
        
        if is_success:
            logger.info(f"登录成功! 用户: {expected_username}")
        else:
            logger.error(f"{error_msg}")
        
        logger.info(f"当前 URL: {page.url}")
        logger.info(f"页面标题: {page.title()}")
        
        screenshot_dir = Path(__file__).parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)
        screenshot_path = screenshot_dir / "login_result.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"截图已保存: {screenshot_path}")
        
        input("\n按 Enter 关闭浏览器...")
        
        browser.close()


if __name__ == "__main__":
    main()
