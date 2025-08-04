# -*- coding: utf-8 -*-
# =====================
#
#
# Author: liumin.423
# Date:   2025/7/7
# =====================
import json
import os
import time

from fastapi import APIRouter
from sse_starlette import ServerSentEvent, EventSourceResponse

from genie_tool.model.code import ActionOutput, CodeOuput
from genie_tool.model.protocal import CIRequest, ReportRequest, DeepSearchRequest, ProjectExplainRequest, VectorSearchRequest
from genie_tool.util.file_util import upload_file
from genie_tool.tool.report import report
from genie_tool.tool.code_interpreter import code_interpreter_agent
from genie_tool.util.middleware_util import RequestHandlerRoute
from genie_tool.tool.deepsearch import DeepSearch
from genie_tool.tool.project_explain import project_explain_async
from genie_tool.tool.vector_search import vector_search

router = APIRouter(route_class=RequestHandlerRoute)


@router.post("/code_interpreter")
async def post_code_interpreter(
    body: CIRequest,
):
     # 处理文件路径
    if body.file_names:
        for idx, f_name in enumerate(body.file_names):
            if not f_name.startswith("/") and not f_name.startswith("http"):
                body.file_names[idx] = f"{os.getenv('FILE_SERVER_URL')}/preview/{body.request_id}/{f_name}"

    async def _stream():
        acc_content = ""
        acc_token = 0
        acc_time = time.time()
        async for chunk in code_interpreter_agent(
            task=body.task,
            file_names=body.file_names,
            request_id=body.request_id,
            stream=True,
        ):


            if isinstance(chunk, CodeOuput):
                yield ServerSentEvent(
                    data=json.dumps(
                        {
                            "requestId": body.request_id,
                            "code": chunk.code,
                            "fileInfo": chunk.file_list,
                            "isFinal": False,
                        },
                        ensure_ascii=False,
                    )
                )
            elif isinstance(chunk, ActionOutput):
                yield ServerSentEvent(
                    data=json.dumps(
                        {
                            "requestId": body.request_id,
                            "codeOutput": chunk.content,
                            "fileInfo": chunk.file_list,
                            "isFinal": True,
                        },
                        ensure_ascii=False,
                    )
                )
                yield ServerSentEvent(data="[DONE]")
            else:
                acc_content += chunk
                acc_token += 1
                if body.stream_mode.mode == "general":
                    yield ServerSentEvent(
                        data=json.dumps(
                            {"requestId": body.request_id, "data": chunk, "isFinal": False},
                            ensure_ascii=False,
                        )
                    )
                elif body.stream_mode.mode == "token":
                    if acc_token >= body.stream_mode.token:
                        yield ServerSentEvent(
                            data=json.dumps(
                                {
                                    "requestId": body.request_id,
                                    "data": acc_content,
                                    "isFinal": False,
                                },
                                ensure_ascii=False,
                            )
                        )
                        acc_token = 0
                        acc_content = ""
                elif body.stream_mode.mode == "time":
                    if time.time() - acc_time > body.stream_mode.time:
                        yield ServerSentEvent(
                            data=json.dumps(
                                {
                                    "requestId": body.request_id,
                                    "data": acc_content,
                                    "isFinal": False,
                                },
                                ensure_ascii=False,
                            )
                        )
                        acc_time = time.time()
                        acc_content = ""
                if body.stream_mode.mode in ["time", "token"] and acc_content:
                    yield ServerSentEvent(
                        data=json.dumps(
                            {
                                "requestId": body.request_id,
                                "data": acc_content,
                                "isFinal": False,
                            },
                            ensure_ascii=False,
                        )
                    )
            

    if body.stream:
        return EventSourceResponse(
            _stream(),
            ping_message_factory=lambda: ServerSentEvent(data="heartbeat"),
            ping=15,
        )
    else:
        content = ""
        async for chunk in code_interpreter_agent(
            task=body.task,
            file_names=body.file_names,
            stream=body.stream,
        ):
            content += chunk
        file_info = [
            await upload_file(
                content=content,
                file_name=body.file_name,
                request_id=body.request_id,
                file_type="html" if body.file_type == "ppt" else body.file_type,
            )
        ]
        return {
            "code": 200,
            "data": content,
            "fileInfo": file_info,
            "requestId": body.request_id,
        }


@router.post("/report")
async def post_report(
    body: ReportRequest,
):
    # 处理文件路径
    if body.file_names:
        for idx, f_name in enumerate(body.file_names):
            if not f_name.startswith("/") and not f_name.startswith("http"):
                body.file_names[idx] = f"{os.getenv('FILE_SERVER_URL')}/preview/{body.request_id}/{f_name}"
    
    def _parser_html_content(content: str):
        if content.startswith("```\nhtml"):
            content = content[len("```\nhtml"): ]
        if content.startswith("```html"):
            content = content[len("```html"): ]
        if content.endswith("```"):
            content = content[: -3]
        return content

    async def _stream():
        content = ""
        acc_content = ""
        acc_token = 0
        acc_time = time.time()
        async for chunk in report(
            task=body.task,
            file_names=body.file_names,
            file_type=body.file_type,
        ):
            content += chunk
            acc_content += chunk
            acc_token += 1
            if body.stream_mode.mode == "general":
                yield ServerSentEvent(
                    data=json.dumps(
                        {"requestId": body.request_id, "data": chunk, "isFinal": False},
                        ensure_ascii=False,
                    )
                )
            elif body.stream_mode.mode == "token":
                if acc_token >= body.stream_mode.token:
                    yield ServerSentEvent(
                        data=json.dumps(
                            {
                                "requestId": body.request_id,
                                "data": acc_content,
                                "isFinal": False,
                            },
                            ensure_ascii=False,
                        )
                    )
                    acc_token = 0
                    acc_content = ""
            elif body.stream_mode.mode == "time":
                if time.time() - acc_time > body.stream_mode.time:
                    yield ServerSentEvent(
                        data=json.dumps(
                            {
                                "requestId": body.request_id,
                                "data": acc_content,
                                "isFinal": False,
                            },
                            ensure_ascii=False,
                        )
                    )
                    acc_time = time.time()
                    acc_content = ""
        if body.stream_mode.mode in ["time", "token"] and acc_content:
            yield ServerSentEvent(
                data=json.dumps({"requestId": body.request_id, "data": acc_content, "isFinal": False},
                                ensure_ascii=False))
        if body.file_type in ["ppt", "html"]:
            content = _parser_html_content(content)
        file_info = [await upload_file(content=content, file_name=body.file_name, request_id=body.request_id,
                                 file_type="html" if body.file_type == "ppt" else body.file_type)]
        yield ServerSentEvent(data=json.dumps(
            {"requestId": body.request_id, "data": content, "fileInfo": file_info,
             "isFinal": True}, ensure_ascii=False))
        yield ServerSentEvent(data="[DONE]")

    if body.stream:
        return EventSourceResponse(
            _stream(),
            ping_message_factory=lambda: ServerSentEvent(data="heartbeat"),
            ping=15,
        )
    else:
        content = ""
        async for chunk in report(
            task=body.task,
            file_names=body.file_names,
            file_type=body.file_type,
        ):
            content += chunk
        if body.file_type in ["ppt", "html"]:
            content = _parser_html_content(content)
        file_info = [await upload_file(content=content, file_name=body.file_name, request_id=body.request_id,
                                 file_type="html" if body.file_type == "ppt" else body.file_type)]
        return {"code": 200, "data": content, "fileInfo": file_info, "requestId": body.request_id}


@router.post("/deepsearch")
async def post_deepsearch(
    body: DeepSearchRequest,
):
    """深度搜索端点"""
    deepsearch = DeepSearch(engines=body.search_engines)
    async def _stream():
        async for chunk in deepsearch.run(
                query=body.query,
                request_id=body.request_id,
                max_loop=body.max_loop,
                stream=True,
                stream_mode=body.stream_mode,
        ):
            yield ServerSentEvent(data=chunk)
        yield ServerSentEvent(data="[DONE]")

    return EventSourceResponse(_stream(), ping_message_factory=lambda: ServerSentEvent(data="heartbeat"), ping=15)


@router.post("/project_explain")
async def post_project_explain(
    body: ProjectExplainRequest,
):
    """代码解释端点"""
    try:
        result = await project_explain_async(
            path=body.path,
            question=body.question,
        )
        return {
            "code": 200,
            "data": result,
            "requestId": body.request_id,
        }
    except Exception as e:
        return {
            "code": 500,
            "data": f"Error: {str(e)}",
            "requestId": body.request_id,
        }


@router.post("/vector_search")
async def post_vector_search(
    body: VectorSearchRequest,
):
    """向量搜索端点"""
    try:
        result = vector_search(
            query_text=body.query_text,
            collection_types=body.collection_types,
            top_k=body.top_k,
            min_score=body.min_score
        )
        return {
            "code": 200,
            "data": result,
            "requestId": body.request_id,
        }
    except Exception as e:
        return {
            "code": 500,
            "data": f"Error: {str(e)}",
            "requestId": body.request_id,
        }

