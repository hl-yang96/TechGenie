package com.jd.genie.agent.tool.common;

import com.alibaba.fastjson.JSONObject;
import com.jd.genie.agent.agent.AgentContext;
import com.jd.genie.agent.dto.CodeInterpreterResponse;
import com.jd.genie.agent.tool.BaseTool;
import com.jd.genie.agent.util.SpringContextHolder;
import com.jd.genie.agent.util.StringUtil;
import com.jd.genie.config.GenieConfig;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.context.ApplicationContext;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import com.jd.genie.agent.tool.common.FileTool;
import com.jd.genie.agent.dto.FileRequest;

@Slf4j
@Data
public class ProjectExplainTool implements BaseTool {
    private AgentContext agentContext;
    private List<String> availableProjects = new ArrayList<>();
    private Map<String, String> projectNameToPath = new HashMap<>();

    @Override
    public String getName() {
        return "project_explain";
    }

    @Override
    public String getDescription() {
        // 加载项目列表
        loadProjectFromGenieTool();

        GenieConfig genieConfig = SpringContextHolder.getApplicationContext().getBean(GenieConfig.class);
        String desc;
        if (genieConfig.getProjectExplainToolDesc().isEmpty()) {
            desc = "此工具是用于对已上传的本地个人程序项目进行分析，并回答关于程序项目中的各类问题，比如软件架构，技术细节，业务流程等。";
        } else {
            desc = genieConfig.getProjectExplainToolDesc();
        }
        desc += "已注册的本地项目包括：[" + String.join(", ", availableProjects) + "]，涉及到这些项目的问题，请使用此工具进行分析，而不是使用 Search 搜索工具。";
        return desc;        
    }

    /**
     * 从 genie-tool 加载项目列表
     */
    private void loadProjectFromGenieTool() {
        try {
            OkHttpClient client = new OkHttpClient.Builder()
                    .connectTimeout(30, TimeUnit.SECONDS)
                    .readTimeout(30, TimeUnit.SECONDS)
                    .build();

            ApplicationContext applicationContext = SpringContextHolder.getApplicationContext();
            GenieConfig genieConfig = applicationContext.getBean(GenieConfig.class);
            String url = genieConfig.getCodeInterpreterUrl() + "/v1/project/list";

            // 构建请求体
            JSONObject requestBody = new JSONObject();
            requestBody.put("limit", 100); // 获取最多100个项目
            requestBody.put("offset", 0);

            RequestBody body = RequestBody.create(
                    MediaType.parse("application/json"),
                    requestBody.toJSONString()
            );

            Request request = new Request.Builder()
                    .url(url)
                    .post(body)
                    .build();

            try (Response response = client.newCall(request).execute()) {
                if (response.isSuccessful() && response.body() != null) {
                    String responseStr = response.body().string();
                    JSONObject jsonResponse = JSONObject.parseObject(responseStr);

                    if (jsonResponse.getBoolean("success")) {
                        com.alibaba.fastjson.JSONArray projects = jsonResponse.getJSONArray("projects");
                        availableProjects.clear();
                        projectNameToPath.clear();

                        for (int i = 0; i < projects.size(); i++) {
                            JSONObject project = projects.getJSONObject(i);
                            String projectName = project.getString("name");
                            String projectPath = project.getString("path");
                            if (projectName != null && !projectName.isEmpty() && projectPath != null && !projectPath.isEmpty()) {
                                availableProjects.add(projectName);
                                projectNameToPath.put(projectName, projectPath);
                                projectNameToPath.put(projectName.toLowerCase(), projectPath);
                            }
                        }

                        log.info("{} loaded {} projects from genie-tool",
                                agentContext != null ? agentContext.getRequestId() : "unknown",
                                availableProjects.size());
                    }
                }
            }
        } catch (Exception e) {
            log.error("{} failed to load projects from genie-tool",
                    agentContext != null ? agentContext.getRequestId() : "unknown", e);
        }
    }

    @Override
    public Map<String, Object> toParams() {
        GenieConfig genieConfig = SpringContextHolder.getApplicationContext().getBean(GenieConfig.class);
        Map<String, Object> parameters;
        if (!genieConfig.getProjectExplainToolParams().isEmpty()) {
            parameters = genieConfig.getProjectExplainToolParams();
        } else {
            Map<String, Object> pathParam = new HashMap<>();
            pathParam.put("type", "string");
            pathParam.put("description", "需要提问的项目名称");

            Map<String, Object> questionParam = new HashMap<>();
            questionParam.put("type", "string");
            questionParam.put("description", "具体问题");

            parameters = new HashMap<>();
            parameters.put("type", "object");
            Map<String, Object> properties = new HashMap<>();
            properties.put("project_name", pathParam);
            properties.put("question", questionParam);
            parameters.put("properties", properties);
            parameters.put("required", Arrays.asList("project_name", "question"));
        }

        if (!availableProjects.isEmpty()) {
            Map<String, Object> properties = (Map<String, Object>) parameters.get("properties");
            Map<String, Object> projectName = (Map<String, Object>) properties.get("project_name");
            projectName.put("description", "项目名称（请从当前已上传的项目中选择，注意大小写：[ " + String.join(", ", availableProjects) + " ]");
        }

        return parameters;
    }

    @Override
    public Object execute(Object input) {
        long startTime = System.currentTimeMillis();

        try {
            Map<String, Object> params = (Map<String, Object>) input;
            String projectName = (String) params.get("project_name");
            String question = (String) params.get("question");

            if (projectName == null || projectName.isEmpty()) {
                String errMessage = "项目名称参数为空，无法进行代码分析。";
                log.error("{} {}", agentContext.getRequestId(), errMessage);
                return errMessage;
            }

            if (question == null || question.isEmpty()) {
                String errMessage = "问题参数为空，无法进行代码分析。";
                log.error("{} {}", agentContext.getRequestId(), errMessage);
                return errMessage;
            }

            // 将项目名称转换为项目路径
            String projectPath = projectNameToPath.get(projectName.toLowerCase());
            if (projectPath == null || projectPath.isEmpty()) {
                String errMessage = "未找到项目 '" + projectName + "' 的路径信息，请确认项目名称是否正确。可用项目: [" + String.join(", ", availableProjects) + "]";
                log.error("{} {}", agentContext.getRequestId(), errMessage);
                return errMessage;
            }

            log.info("{} converting project name '{}' to path '{}'", agentContext.getRequestId(), projectName, projectPath);

            ProjectExplainRequest request = ProjectExplainRequest.builder()
                    .requestId(agentContext.getSessionId())
                    .path(projectPath)
                    .question(question)
                    .build();

            // 调用 API
            Future future = callProjectExplainApi(request);
            Object object = future.get();

            return object;
        } catch (Exception e) {
            log.error("{} project_explain error", agentContext.getRequestId(), e);
        }
        return null;
    }

    /**
     * 调用 ProjectExplain API
     */
    public CompletableFuture<String> callProjectExplainApi(ProjectExplainRequest projectExplainRequest) {
        CompletableFuture<String> future = new CompletableFuture<>();
        try {
            OkHttpClient client = new OkHttpClient.Builder()
                    .connectTimeout(60, TimeUnit.SECONDS) // 设置连接超时时间为 1 分钟
                    .readTimeout(600, TimeUnit.SECONDS)    // 设置读取超时时间为 10 分钟
                    .writeTimeout(600, TimeUnit.SECONDS)   // 设置写入超时时间为 10 分钟
                    .callTimeout(600, TimeUnit.SECONDS)    // 设置调用超时时间为 10 分钟
                    .build();

            ApplicationContext applicationContext = SpringContextHolder.getApplicationContext();
            GenieConfig genieConfig = applicationContext.getBean(GenieConfig.class);
            String url = genieConfig.getCodeInterpreterUrl() + "/v1/tool/project_explain";
            RequestBody body = RequestBody.create(
                    MediaType.parse("application/json"),
                    JSONObject.toJSONString(projectExplainRequest)
            );

            log.info("{} project_explain request {}", agentContext.getRequestId(), JSONObject.toJSONString(projectExplainRequest));
            Request.Builder requestBuilder = new Request.Builder()
                    .url(url)
                    .post(body);
            Request request = requestBuilder.build();

            try (Response response = client.newCall(request).execute()) {
                log.info("{} project_explain response {} {}", agentContext.getRequestId(), response.code(), response.body());

                if (!response.isSuccessful()) {
                    String errorMsg = "project_explain 请求失败，状态码: " + response.code();
                    log.error("{} {}", agentContext.getRequestId(), errorMsg);
                    future.complete(errorMsg);
                    return future;
                }

                ResponseBody responseBody = response.body();
                if (responseBody == null) {
                    String errorMsg = "project_explain 响应体为空";
                    log.error("{} {}", agentContext.getRequestId(), errorMsg);
                    future.complete(errorMsg);
                    return future;
                }

                String responseStr = responseBody.string();
                JSONObject jsonResponse = JSONObject.parseObject(responseStr);

                if (jsonResponse.getIntValue("code") == 200) {
                    String result = jsonResponse.getString("data");
                    
                    // 保存项目分析结果到文件
                    saveProjectExplainResult(projectExplainRequest.getPath(), 
                                            projectExplainRequest.getQuestion(), 
                                            result);
                    
                    future.complete(result);
                } else {
                    String errorMsg = "project_explain 执行失败: " + jsonResponse.getString("data");
                    log.error("{} {}", agentContext.getRequestId(), errorMsg);
                    future.complete(errorMsg);
                }
            } catch (IOException e) {
                log.error("{} project_explain request error", agentContext.getRequestId(), e);
                future.completeExceptionally(e);
            }
        } catch (Exception e) {
            log.error("{} project_explain request error", agentContext.getRequestId(), e);
            future.completeExceptionally(e);
        }

        return future;
    }

    /**
     * ProjectExplain 请求类
     */
    @lombok.Builder
    @lombok.Data
    public static class ProjectExplainRequest {
        private String requestId;
        private String path;
        private String question;
    }

    /**
     * 保存项目分析结果到文件
     */
    private void saveProjectExplainResult(String path, String question, String result) {
        try {
            FileTool fileTool = new FileTool();
            fileTool.setAgentContext(agentContext);
            
            // 构建文件内容
            StringBuilder content = new StringBuilder();
            content.append("# 项目分析结果\n\n");
            content.append("**项目路径**: ").append(path).append("\n\n");
            content.append("**分析问题**: ").append(question).append("\n\n");
            content.append("**分析结果**:\n").append(result).append("\n");
            
            // 生成文件名
            String fileName = StringUtil.removeSpecialChars("项目分析_" + question.substring(0, Math.min(question.length(), 10)) + ".md");
            String fileDesc = "项目分析: " + question.substring(0, Math.min(question.length(), 50)) + "...";
            
            FileRequest fileRequest = FileRequest.builder()
                    .requestId(agentContext.getRequestId())
                    .fileName(fileName)
                    .description(fileDesc)
                    .content(content.toString())
                    .build();
            
            fileTool.uploadFile(fileRequest, true, false); // isInternalFile=false, 作为产品文件
            
            CodeInterpreterResponse codeResponse = CodeInterpreterResponse.builder()
                .requestsId(agentContext.getRequestId())
                .isFinal(false)
                .content(content.toString())
                .data(content.toString())
                .build();
            agentContext.getPrinter().send(agentContext.getRequestId(), "markdown", codeResponse, null, false);

            log.info("{} project_explain result saved to file: {}", agentContext.getRequestId(), fileName);
        } catch (Exception e) {
            log.error("{} failed to save project_explain result to file", agentContext.getRequestId(), e);
        }
    }
}
