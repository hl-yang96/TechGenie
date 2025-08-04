package com.jd.genie.agent.tool.common;

import com.alibaba.fastjson.JSONObject;
import com.jd.genie.agent.agent.AgentContext;
import com.jd.genie.agent.tool.BaseTool;
import com.jd.genie.agent.util.SpringContextHolder;
import com.jd.genie.config.GenieConfig;
import com.jd.genie.agent.tool.common.FileTool;
import com.jd.genie.agent.dto.FileRequest;
import com.jd.genie.agent.util.StringUtil;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import okhttp3.*;
import org.springframework.context.ApplicationContext;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

/**
 * 向量搜索工具
 * 用于在文档知识库中进行语义相似度搜索
 */
@Slf4j
@Data
public class VectorSearchTool implements BaseTool {
    private AgentContext agentContext;

    @Override
    public String getName() {
        return "vector_search";
    }

    @Override
    public String getDescription() {
        String desc = "这个工具用于在文档知识库中进行语义相似度搜索，可以根据查询文本找到相关的文档内容，支持设置相似度阈值和结果数量。尤其适用于查找项目经验、技能知识、简历信息等场景。";
        GenieConfig genieConfig = SpringContextHolder.getApplicationContext().getBean(GenieConfig.class);
        return genieConfig.getVectorSearchToolDesc().isEmpty() ? desc : genieConfig.getVectorSearchToolDesc();
    }

    @Override
    public Map<String, Object> toParams() {
        GenieConfig genieConfig = SpringContextHolder.getApplicationContext().getBean(GenieConfig.class);
        if (!genieConfig.getVectorSearchToolParams().isEmpty()) {
            return genieConfig.getVectorSearchToolParams();
        }

        Map<String, Object> queryTextParam = new HashMap<>();
        queryTextParam.put("type", "string");
        queryTextParam.put("description", "搜索查询文本，描述要查找的内容");

        Map<String, Object> collectionTypesParam = new HashMap<>();
        collectionTypesParam.put("type", "array");
        collectionTypesParam.put("items", Map.of("type", "string"));
        collectionTypesParam.put("description", "要搜索的集合类型列表，可选值：projects_experience, resumes, job_postings。为空则搜索所有集合");

        Map<String, Object> topKParam = new HashMap<>();
        topKParam.put("type", "integer");
        topKParam.put("description", "返回匹配度最高的N个结果，默认10");
        topKParam.put("default", 10);

        Map<String, Object> minScoreParam = new HashMap<>();
        minScoreParam.put("type", "number");
        minScoreParam.put("description", "最小相似度分数阈值（0-1），默认0.4，建议设置 0.5以下");
        minScoreParam.put("default", 0.4);

        Map<String, Object> parameters = new HashMap<>();
        parameters.put("type", "object");
        Map<String, Object> properties = new HashMap<>();
        properties.put("query_text", queryTextParam);
        properties.put("collection_types", collectionTypesParam);
        properties.put("top_k", topKParam);
        properties.put("min_score", minScoreParam);
        parameters.put("properties", properties);
        parameters.put("required", Arrays.asList("query_text"));

        return parameters;
    }

    @Override
    public Object execute(Object input) {
        long startTime = System.currentTimeMillis();

        try {
            Map<String, Object> params = (Map<String, Object>) input;
            String queryText = (String) params.get("query_text");
            List<String> collectionTypes = (List<String>) params.get("collection_types");
            Integer topK = params.get("top_k") != null ? ((Number) params.get("top_k")).intValue() : 5;
            Double minScore = params.get("min_score") != null ? ((Number) params.get("min_score")).doubleValue() : 0.4;

            if (queryText == null || queryText.isEmpty()) {
                String errMessage = "查询文本参数为空，无法进行向量搜索。";
                log.error("{} {}", agentContext.getRequestId(), errMessage);
                return errMessage;
            }

            VectorSearchRequest request = VectorSearchRequest.builder()
                    .requestId(agentContext.getSessionId())
                    .queryText(queryText)
                    .collectionTypes(collectionTypes)
                    .topK(topK)
                    .minScore(minScore)
                    .build();

            // 调用 API
            Future future = callVectorSearchApi(request);
            Object object = future.get();

            return object;
        } catch (Exception e) {
            log.error("{} vector_search error", agentContext.getRequestId(), e);
        }
        return null;
    }

    /**
     * 调用 VectorSearch API
     */
    public CompletableFuture<String> callVectorSearchApi(VectorSearchRequest vectorSearchRequest) {
        CompletableFuture<String> future = new CompletableFuture<>();
        try {
            OkHttpClient client = new OkHttpClient.Builder()
                    .connectTimeout(10, TimeUnit.SECONDS) // 设置连接超时时间为 1 分钟
                    .readTimeout(60, TimeUnit.SECONDS)    // 设置读取超时时间为 5 分钟
                    .writeTimeout(60, TimeUnit.SECONDS)   // 设置写入超时时间为 5 分钟
                    .callTimeout(60, TimeUnit.SECONDS)    // 设置调用超时时间为 5 分钟
                    .build();

            ApplicationContext applicationContext = SpringContextHolder.getApplicationContext();
            GenieConfig genieConfig = applicationContext.getBean(GenieConfig.class);
            String url = genieConfig.getCodeInterpreterUrl() + "/v1/tool/vector_search";
            RequestBody body = RequestBody.create(
                    MediaType.parse("application/json"),
                    JSONObject.toJSONString(vectorSearchRequest)
            );

            log.info("{} vector_search request {}", agentContext.getRequestId(), JSONObject.toJSONString(vectorSearchRequest));
            Request.Builder requestBuilder = new Request.Builder()
                    .url(url)
                    .post(body);
            Request request = requestBuilder.build();

            client.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    log.error("{} vector_search request failed", agentContext.getRequestId(), e);
                    future.completeExceptionally(e);
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    try (ResponseBody responseBody = response.body()) {
                        if (!response.isSuccessful()) {
                            String errorMsg = "vector_search 请求失败: HTTP " + response.code();
                            log.error("{} {}", agentContext.getRequestId(), errorMsg);
                            future.complete(errorMsg);
                            return;
                        }

                        String responseStr = responseBody.string();
                        JSONObject jsonResponse = JSONObject.parseObject(responseStr);

                        if (jsonResponse.getIntValue("code") == 200) {
                            Object data = jsonResponse.get("data");
                            
                            String result;
                            if (data instanceof JSONObject) {
                                JSONObject dataObj = (JSONObject) data;
                                if (dataObj.getBooleanValue("success")) {
                                    // 格式化搜索结果为可读文本
                                    result = formatSearchResults(dataObj);
                                    
                                } else {
                                    result = "向量搜索失败: " + dataObj.getString("error");
                                    log.error("{} 向量搜索失败: {}", agentContext.getRequestId(), result);
                                }
                            } else {
                                result = data.toString();
                            }
                            
                            // 保存向量搜索结果到文件
                            saveVectorSearchResult(vectorSearchRequest.getQueryText(), 
                                                 vectorSearchRequest.getCollectionTypes(),
                                                 result, jsonResponse);
                            
                            future.complete(result);
                        } else {
                            String errorMsg = "vector_search 执行失败: " + jsonResponse.getString("data");
                            log.error("{} {}", agentContext.getRequestId(), errorMsg);
                            future.complete(errorMsg);
                        }
                    } catch (Exception e) {
                        log.error("{} vector_search response parsing error", agentContext.getRequestId(), e);
                        future.completeExceptionally(e);
                    }
                }
            });
        } catch (Exception e) {
            log.error("{} vector_search request error", agentContext.getRequestId(), e);
            future.completeExceptionally(e);
        }

        return future;
    }

    /**
     * 格式化搜索结果为可读文本
     */
    private String formatSearchResults(JSONObject dataObj) {
        try {
            List<Object> results = dataObj.getJSONArray("results");
            int totalResults = dataObj.getIntValue("total_results");
            String query = dataObj.getString("query");
            Double minScore = dataObj.getDouble("min_score_used");

            if (results == null || results.isEmpty()) {
                return String.format("未找到与查询 \"%s\" 相关的文档（最小相似度阈值: %.2f）。建议降低相似度阈值或检查文档是否已摄取到知识库中。", 
                    query, minScore);
            }

            StringBuilder sb = new StringBuilder();
            sb.append(String.format("找到 %d 条与查询 \"%s\" 相关的文档:\n\n", totalResults, query));

            for (int i = 0; i < results.size(); i++) {
                JSONObject result = (JSONObject) results.get(i);
                String content = result.getString("content");
                Double score = result.getDouble("score");
                String collectionType = result.getString("collection_type");
                // get from metadata.file_name
                JSONObject metadata = (JSONObject)result.get("metadata");
                String source = metadata != null ? metadata.getString("file_name") : "unknown";

                // 截断过长的内容
                if (content.length() > 1500) {
                    content = content.substring(0, 1500) + "...";
                }

                sb.append(String.format("%d. [相似度: %.3f] [类型: %s] [来源: %s]\n", i + 1, score, collectionType, source));
                sb.append(String.format("   %s\n\n", content));
            }

            return sb.toString().trim();
        } catch (Exception e) {
            log.error("{} format search results error", agentContext.getRequestId(), e);
            return "搜索结果格式化失败: " + e.getMessage();
        }
    }

    /**
     * VectorSearch 请求类
     */
    @lombok.Builder
    @lombok.Data
    public static class VectorSearchRequest {
        private String requestId;
        private String queryText;
        private List<String> collectionTypes;
        private Integer topK;
        private Double minScore;
    }

    /**
     * 保存向量搜索结果到文件
     */
    private void saveVectorSearchResult(String queryText, List<String> collectionTypes, 
                                      String result, JSONObject jsonResponse) {
        try {
            FileTool fileTool = new FileTool();
            fileTool.setAgentContext(agentContext);
            
            // 构建文件内容
            StringBuilder content = new StringBuilder();
            content.append("# 向量搜索结果\n");
            content.append("**搜索关键字**: ").append(queryText).append("\n");
            
            if (collectionTypes != null && !collectionTypes.isEmpty()) {
                content.append("**搜索集合**: ").append(String.join(", ", collectionTypes)).append("\n");
            }
            content.append("**搜索结果**: ").append(result).append("\n");

            // 生成文件名
            String fileName = StringUtil.removeSpecialChars("向量搜索_" + queryText.substring(0, Math.min(queryText.length(), 10)) + ".md");
            String fileDesc = "向量搜索: " + queryText.substring(0, Math.min(queryText.length(), 50)) + "...";
            
            FileRequest fileRequest = FileRequest.builder()
                    .requestId(agentContext.getRequestId())
                    .fileName(fileName)
                    .description(fileDesc)
                    .content(content.toString())
                    .build();
            
            fileTool.uploadFile(fileRequest, true, false); // isInternalFile=false, 作为产品文件
            
            log.info("{} vector_search result saved to file: {}", agentContext.getRequestId(), fileName);
        } catch (Exception e) {
            log.error("{} failed to save vector_search result to file", agentContext.getRequestId(), e);
        }
    }
}
