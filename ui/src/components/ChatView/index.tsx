import { useEffect, useState, useRef, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { getUniqId, scrollToTop, ActionViewItemEnum, getSessionId } from "@/utils";
import { sessionApi } from "@/services/session";
import querySSE from "@/utils/querySSE";
import {  handleTaskData, combineData } from "@/utils/chat";
import Dialogue from "@/components/Dialogue";
import GeneralInput from "@/components/GeneralInput";
import ActionView from "@/components/ActionView";
import ChatHistory from "@/components/ChatHistory";
import { FileInfo, fileApi } from "@/services/file";
import { RESULT_TYPES } from '@/utils/constants';
import { useMemoizedFn } from "ahooks";
import classNames from "classnames";
import Logo from "../Logo";
import { Modal } from "antd";

type Props = {
  inputInfo: CHAT.TInputInfo;
  product?: CHAT.Product;
  requestId?: string;
};

const ChatView: GenieType.FC<Props> = (props) => {
  const { inputInfo: inputInfoProp, product, requestId: propRequestId } = props;
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [chatTitle, setChatTitle] = useState("");
  const [taskList, setTaskList] = useState<MESSAGE.Task[]>([]);
  const chatList = useRef<CHAT.ChatItem[]>([]);
  const [activeTask, setActiveTask] = useState<CHAT.Task>();
  const [plan, setPlan] = useState<CHAT.Plan>();
  const [showAction, setShowAction] = useState(false);
  const [loading, setLoading] = useState(false);
  const chatRef = useRef<HTMLInputElement>(null);
  const actionViewRef = ActionView.useActionView();
  const sessionId = useMemo(() => getSessionId(), []);
  const [modal, contextHolder] = Modal.useModal();
  const [hasNavigated, setHasNavigated] = useState(false);
  const [isFromUrl, setIsFromUrl] = useState(false);
  const [hasInitialized, setHasInitialized] = useState(false);
  const [currentSSEConnection, setCurrentSSEConnection] = useState<any>(null);
  const [hasSavedSession, setHasSavedSession] = useState(false);
  const [showHistorySidebar, setShowHistorySidebar] = useState(true);
  const hasSavedSessionRef = useRef(false);

  // 当有 propRequestId 时，加载对应的聊天会话
  useEffect(() => {
    if (propRequestId) {
      setIsFromUrl(true);
      console.log('Loading chat session for requestId:', propRequestId);
      loadChatSession(propRequestId);
    }
  }, [propRequestId]);



  // 处理初始消息发送
  useEffect(() => {
    // 只有当不是从 URL 加载且有真实的用户输入且还没有初始化过时才发送消息
    if (!propRequestId && inputInfoProp.message && inputInfoProp.message.trim() !== "" && !hasInitialized) {
      setHasInitialized(true);
      sendMessage(inputInfoProp);
    }
  }, [inputInfoProp.message, propRequestId, hasInitialized]);

  // 处理查看历史会话文件
  const handleViewHistoryFiles = useMemoizedFn(async (reqId: string, files: FileInfo[]) => {
    try {
      // 先清空之前的文件列表
      setTaskList([]);

      // 首先加载历史会话数据
      const sessionResult = await sessionApi.getSession({ reqId });

      if (sessionResult.success && sessionResult.data) {
        // 恢复聊天数据
        const { chatList: savedChatList, chatTitle: savedTitle } = sessionResult.data;
        if (savedChatList) {
          // 过滤掉loading状态和tip，因为这是历史数据
          const historyChatList = savedChatList.map((chat: any) => ({
            ...chat,
            loading: false,
            tip: undefined,
            // 确保显示完整的response（包括responseAll）
            response: chat.response || chat.responseAll || chat.response
          }));
          chatList.current = historyChatList;
        }
        if (savedTitle) {
          setChatTitle(savedTitle);
        }
      }
    } catch (error) {
      console.error('Error loading chat session:', error);
    }

    // 转换文件格式为工作空间组件需要的格式
    const taskList: MESSAGE.Task[] = files.map((file, index) => ({
      messageTime: new Date().toISOString(),
      messageType: 'file',
      resultMap: {
        fileInfo: [{
          fileName: file.fileName,
          ossUrl: file.ossUrl,
          fileSize: 0, // 历史文件大小未知，设为0
          domainUrl: file.domainUrl
        }],
        steps: []
      },
      requestId: reqId,
      messageId: `${reqId}-${index}`,
      finish: true,
      isFinal: true,
      id: `${reqId}-${index}`
    }));

    // 设置任务列表并显示工作空间
    setTaskList(taskList);
    setShowAction(true);
    actionViewRef.current?.changeActionView(ActionViewItemEnum.file);
  });

  // 加载聊天会话数据
  const loadChatSession = async (reqId: string) => {
    try {
      const result = await sessionApi.getSession({ reqId });

      if (result.success && result.data) {
        // 恢复聊天数据
        const { chatList: savedChatList, chatTitle: savedTitle } = result.data;
        if (savedChatList) {
          // 确保历史数据正确显示，包括responseAll
          const historyChatList = savedChatList.map((chat: any) => ({
            ...chat,
            loading: false,
            tip: undefined,
            // 确保显示完整的response（包括responseAll）
            response: chat.response || chat.responseAll || ""
          }));
          chatList.current = historyChatList;
        }
        if (savedTitle) {
          setChatTitle(savedTitle);
        }
        console.log('Chat session loaded successfully');

        // 如果是从历史对话进入，自动加载文件并展开工作空间
        const fromHistory = searchParams.get('from') === 'history';
        if (fromHistory) {
          try {
            const fileResponse = await fileApi.getFileList({ requestId: reqId });
            if (fileResponse.results && fileResponse.results.length > 0) {
              handleViewHistoryFiles(reqId, fileResponse.results);
            } else {
              // 如果没有文件，清空之前的文件列表并隐藏工作空间
              setTaskList([]);
              setShowAction(false);
            }
          } catch (fileError) {
            console.error('Error loading files for history session:', fileError);
            // 出错时也清空文件列表
            setTaskList([]);
            setShowAction(false);
          }
        }
      }
    } catch (error) {
      console.error('Error loading chat session:', error);
    }
  };

  // 保存聊天会话到后端
  const saveChatSession = async (reqId: string, chatData: any) => {
    try {
      console.log('Saving chat session for reqId:', reqId, 'with data:', chatData);
      const result = await sessionApi.createSession({
        reqId,
        data: chatData
      });

      if (!result.success) {
        console.error('Failed to save chat session:', result.message);
      } else {
        console.log('Chat session saved successfully for reqId:', reqId);
      }
    } catch (error: any) {
      console.error('Error saving chat session for reqId:', reqId, error);
      // 如果是409冲突错误（会话已存在），这是正常的，不需要报错
      if (error?.response?.status === 409) {
        console.log('Session already exists for reqId:', reqId);
      }
    }
  };

  // 更新聊天会话到后端
  const updateChatSession = async (reqId: string, chatData: any) => {
    try {
      console.log('Updating chat session for reqId:', reqId, 'with data:', chatData);
      const result = await sessionApi.updateSession({
        reqId,
        data: chatData
      });

      if (!result.success) {
        console.error('Failed to update chat session:', result.message);
      } else {
        console.log('Chat session updated successfully for reqId:', reqId);
      }
    } catch (error: any) {
      console.error('Error updating chat session for reqId:', reqId, error);
    }
  };

  const combineCurrentChat = (
    inputInfo: CHAT.TInputInfo,
    sessionId: string,
    requestId: string
  ): CHAT.ChatItem => {
    return {
      query: inputInfo.message!,
      files: inputInfo.files!,
      responseType: "txt",
      sessionId,
      requestId,
      loading: true,
      forceStop: false,
      tasks: [],
      thought: "",
      response: "",
      taskStatus: 0,
      tip: "已接收到你的任务，将立即开始处理...",
      multiAgent: {tasks: []},
    };
  };

  const sendMessage = useMemoizedFn((inputInfo: CHAT.TInputInfo) => {
    const {message, deepThink, outputStyle} = inputInfo;

    // 如果是从 URL 加载的会话且没有真实的用户输入，不发送请求
    if (propRequestId && (!message || message.trim() === "")) {
      return;
    }

    const requestId = getUniqId();
    let currentChat = combineCurrentChat(inputInfo, sessionId, requestId);
    chatList.current =  [...chatList.current, currentChat];
    if (!chatTitle) {
      setChatTitle(message!);
    }

    // 重置会话保存状态，为新的请求做准备
    setHasSavedSession(false);
    setHasNavigated(false);
    hasSavedSessionRef.current = false;

    setLoading(true);
    const params = {
      sessionId: sessionId,
      requestId: requestId,
      query: message,
      deepThink: deepThink ? 1 : 0,
      outputStyle
    };
    const handleMessage = (data: MESSAGE.Answer) => {
      const { finished, resultMap, packageType, status, reqId, responseAll } = data;

      // 当收到 reqId 且还没有导航过时，导航到新的 URL 并保存会话
      if (reqId && !hasNavigated && !propRequestId && !hasSavedSessionRef.current) {
        console.log('First time receiving reqId, saving session:', reqId);
        hasSavedSessionRef.current = true; // 立即标记，防止重复
        setHasNavigated(true);
        setHasSavedSession(true);
        // 保存当前聊天数据到后端（只保存一次）
        saveChatSession(reqId, {
          chatList: chatList.current,
          sessionId: sessionId,
          chatTitle: chatTitle || (chatList.current[0]?.query)
        });
        // 导航到新的 URL，但不替换历史记录，这样用户可以返回
        navigate(`/${reqId}`);
      } else if (reqId && hasSavedSessionRef.current) {
        console.log('Session already saved for reqId:', reqId, 'skipping...');
      }
      if (status === "tokenUseUp") {
        modal.info({
          title: '您的试用次数已用尽',
          content: '如需额外申请，请联系 liyang.1236@jd.com',
        });
        const taskData = handleTaskData(
          currentChat,
          deepThink,
          currentChat.multiAgent
        );
        currentChat.loading = false;
        setLoading(false);

        setTaskList(taskData.taskList);
        return;
      }
      if (packageType !== "heartbeat") {
        requestAnimationFrame(() => {
          if (resultMap?.eventData) {
            currentChat = combineData(resultMap.eventData || {}, currentChat);
            const taskData = handleTaskData(
              currentChat,
              deepThink,
              currentChat.multiAgent
            );
            setTaskList(taskData.taskList);
            updatePlan(taskData.plan!);
            openAction(taskData.taskList);
            if (finished) {
              currentChat.loading = false;
              setLoading(false);

              // 当任务完成时，更新数据库中的会话数据
              if (status === "success" && reqId && responseAll) {
                console.log('Task finished, updating session with responseAll:', responseAll);
                // 更新当前聊天项的response
                currentChat.response = responseAll;
                // 更新数据库中的会话数据
                updateChatSession(reqId, {
                  chatList: [...chatList.current.slice(0, -1), currentChat], // 更新最后一个聊天项
                  sessionId: sessionId,
                  chatTitle: chatTitle || (chatList.current[0]?.query)
                });
              }
            }
            const newChatList = [...chatList.current];
            newChatList.splice(newChatList.length - 1, 1, currentChat);
            chatList.current = newChatList;
          }
        });
        scrollToTop(chatRef.current!);
      }
    };

    const openAction = (taskList:MESSAGE.Task[]) =>{
      if (taskList.filter((t)=>!RESULT_TYPES.includes(t.messageType)).length) {
        setShowAction(true);
      }
    };

    const handleError = (error: unknown) => {
      throw error;
    };

    const handleClose = () => {
      console.log('🚀 ~ close');
    };

    querySSE({
      body: params,
      handleMessage,
      handleError,
      handleClose,
    });
  });

  const changeTask = (task: CHAT.Task) => {
    actionViewRef.current?.changeActionView(ActionViewItemEnum.follow);
    changeActionStatus(true);
    setActiveTask(task);
  };

  const updatePlan = (plan: CHAT.Plan) => {
    setPlan(plan);
  };

  const changeFile = (file: CHAT.TFile) => {
    changeActionStatus(true);
    actionViewRef.current?.setFilePreview(file);
  };

  const changePlan = () => {
    changeActionStatus(true);
    actionViewRef.current?.openPlanView();
  };

  const changeActionStatus = (status: boolean) => {
    setShowAction(status);
  };



  // 切换历史对话侧边栏显示状态
  const toggleHistorySidebar = useMemoizedFn(() => {
    setShowHistorySidebar(!showHistorySidebar);
  });



  return (
    <div className="h-full w-full flex">
      {/* 历史对话侧边栏 */}
      {showHistorySidebar && (
        <div className="w-[300px] border-r border-gray-200 flex-shrink-0">
          <ChatHistory
            currentReqId={propRequestId}
          />
        </div>
      )}

      <div className="flex-1 flex justify-center">
        <div
          className={classNames("p-24 flex flex-col flex-1 w-0", {
            'max-w-[1200px]': !showAction,
            'max-w-[450px]': showAction && searchParams.get('from') === 'history'
          })}
          id="chat-view"
        >
          <div className="w-full flex justify-between">
            <div className="w-full flex items-center pb-8">
              {/* 历史对话按钮 */}
              <div
                className="mr-12 cursor-pointer p-8 rounded hover:bg-gray-100 transition-colors flex items-center"
                onClick={toggleHistorySidebar}
                title={showHistorySidebar ? "隐藏历史对话" : "显示历史对话"}
              >
                <span className="text-sm text-gray-600">
                  {showHistorySidebar ? '◀' : '▶'} 历史
                </span>
              </div>

              <Logo />
              <div className="overflow-hidden whitespace-nowrap text-ellipsis text-[16px] font-[500] text-[#27272A] mr-8">
                {chatTitle}
              </div>
              {inputInfoProp.deepThink && <div className="rounded-[4px] px-6 border-1 border-solid border-gray-300 flex items-center shrink-0">
                <i className="font_family icon-shendusikao mr-6 text-[12px]"></i>
                <span className="ml-[-4px]">深度研究</span>
              </div>}
            </div>
          </div>
        <div
          className="w-full flex-1 overflow-auto no-scrollbar mb-[36px]"
          ref={chatRef}
        >
          {chatList.current.map((chat) => {
            return <div key={chat.requestId}>
              <Dialogue
                chat={chat}
                deepThink={inputInfoProp.deepThink}
                changeTask={changeTask}
                changeFile={changeFile}
                changePlan={changePlan}
              />
            </div>;
          })}
        </div>
        <GeneralInput
          placeholder={loading ? "任务进行中" : "希望 Genie 为你做哪些任务呢？"}
          showBtn={false}
          size="medium"
          disabled={loading}
          product={product}
          // 多轮问答也不支持切换deepThink，使用传进来的
          send={(info) => sendMessage({
            ...info,
            deepThink: inputInfoProp.deepThink
          })}
        />
      </div>
      {contextHolder}
      <div className={classNames('transition-all w-0', {
        'opacity-0 overflow-hidden': !showAction,
        'flex-1': showAction,
      })}>
        <ActionView
          activeTask={activeTask}
          taskList={taskList}
          plan={plan}
          ref={actionViewRef}
          onClose={() => changeActionStatus(false)}
        />
      </div>
      </div>
    </div>
  );
};

export default ChatView;
