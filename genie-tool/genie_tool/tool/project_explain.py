# -*- coding: utf-8 -*-
# =====================
#
#
# Author: liumin.423
# Date:   2025/7/28
# =====================
import os
import asyncio
from genie_tool.util.prompt_util import get_prompt

try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


async def project_explain_async(path: str, question: str) -> str:
    """
    代码解释工具 - 异步版本
    Args:
        path: 需要分析的项目的绝对路径
        question: 具体问题
    Returns:
        分析结果
    """
    try:
        # 验证路径是否存在
        if not os.path.exists(path):
            error_msg = f"Error: 路径 {path} 不存在"
            logger.error(error_msg)
            return error_msg

        if not os.path.isdir(path):
            error_msg = f"Error: {path} 不是一个目录"
            logger.error(error_msg)
            return error_msg

        # 构建命令
        question = question.replace('"', '\"').replace("'", '\'')
        prompt_template = get_prompt("project_explain")["project_explain_prompt"]
        prompt = prompt_template.format(question=question)
        prompt.replace('"', '\"')
        command = f'cd "{path}"; https_proxy="http://127.0.0.1:7890" http_proxy="http://127.0.0.1:7890" all_proxy="socks5://127.0.0.1:7890" gemini -p "{prompt}"'

        logger.info(f"Executing async command: {command}")

        # 使用 asyncio.create_subprocess_shell 执行命令
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=None
        )

        try:
            # 等待进程完成，设置5分钟超时
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=300)

            if process.returncode != 0:
                error_msg = f"Command failed with return code: {process.returncode}\nOutput: {stdout.decode()}"
                logger.error(error_msg)
                return error_msg

            res = stdout.decode().strip()
            logger.info(f"Async project explain command executed successfully")
            return res

        except asyncio.TimeoutError:
            # 超时时杀死进程
            process.kill()
            await process.wait()
            error_msg = "Command timed out after 5 minutes"
            logger.error(error_msg)
            return error_msg

    except Exception as e:
        error_msg = f"Error executing async project_explain: {str(e)}"
        logger.error(error_msg)
        return error_msg


if __name__ == "__main__":
    pass
