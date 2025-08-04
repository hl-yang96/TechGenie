import { useState, useCallback, memo, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import GeneralInput from "@/components/GeneralInput";
import Slogn from "@/components/Slogn";
import ChatView from "@/components/ChatView";
import { productList, defaultProduct } from "@/utils/constants";
import { Image } from "antd";
import { demoList } from "@/utils/constants";

type HomeProps = Record<string, never>;

const Home: GenieType.FC<HomeProps> = memo(() => {
  const { requestId } = useParams<{ requestId?: string }>();
  const navigate = useNavigate();
  const [inputInfo, setInputInfo] = useState<CHAT.TInputInfo>({
    message: "",
    deepThink: false,
  });
  const [product, setProduct] = useState(defaultProduct);
  const [videoModalOpen, setVideoModalOpen] = useState();
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [pendingMessage, setPendingMessage] = useState<CHAT.TInputInfo | null>(null);

  const changeInputInfo = useCallback((info: CHAT.TInputInfo) => {
    setInputInfo(info);
  }, []);

  // 当有 requestId 时，加载对应的聊天会话
  useEffect(() => {
    console.log('Home: requestId changed to:', requestId);
    if (requestId) {
      setIsLoadingSession(true);
      // 从 URL 参数加载时，不设置 inputInfo.message，避免触发新的请求
      // ChatView 会根据 requestId 来判断是否是从 URL 加载的会话
      setIsLoadingSession(false);
    } else {
      // 当没有 requestId 时（回到主页），重置 inputInfo 状态
      console.log('Home: No requestId, resetting inputInfo');
      setInputInfo({
        message: "",
        deepThink: false,
      });
    }
  }, [requestId]);

  const CaseCard = ({ title, description, tag, image, url, videoUrl }: any) => {
    const handleReportClick = () => {
      window.open(url, '_blank');
    };

    const hasVideo = videoUrl && videoUrl.trim() !== '';

    return (
      <div className="group flex flex-col rounded-lg bg-white pt-16 px-16 shadow-[0_4px_12px_rgba(0,0,0,0.05)] hover:shadow-[0_8px_20px_rgba(0,0,0,0.1)] hover:-translate-y-[5px] transition-all duration-300 ease-in-out cursor-pointer w-full max-w-xs border border-[rgba(233,233,240,1)]">
        <div className="mb-4 flex items-center justify-between">
          <div className="text-[14px] font-bold truncate">{title}</div>
          <div className="shrink-0 inline-block bg-gray-100 text-gray-600 px-[6px] leading-[20px] text-[12px] rounded-[4px]">
            {tag}
          </div>
        </div>
        <div className="text-[12px] text-[#71717a] h-40 line-clamp-2 leading-[20px]">
          {description}
        </div>
        <div
          className="text-[#4040ff] group-hover:text-[#656cff] text-[12px] flex items-center mb-6 cursor-pointer transition-colors duration-200"
          onClick={handleReportClick}
        >
          <span className="mr-1">查看报告</span>
          <i className="font_family icon-xinjianjiantou"></i>
        </div>
        <div className="relative rounded-t-[10px] overflow-hidden h-100 group-hover:scale-105 transition-transform duration-500 ease">
          {hasVideo && (
            <Image
              style={{ display: "none" }}
              preview={{
                visible: videoModalOpen === videoUrl,
                destroyOnHidden: true,
                imageRender: () => (
                  <video muted width="80%" controls autoPlay src={videoUrl} />
                ),
                toolbarRender: () => null,
                onVisibleChange: () => {
                  setVideoModalOpen(undefined);
                },
              }}
              src={image}
            />
          )}
          <img
            src={image}
            className="w-full h-full rounded-t-[10px] mt-[-20px]"
          ></img>
          {hasVideo && (
            <div
              className="absolute inset-0 flex items-center justify-center cursor-pointer rounded-t-[10px] group hover:bg-[rgba(0,0,0,0.6)] border border-[#ededed]"
              onClick={() => setVideoModalOpen(videoUrl)}
            >
              <i className="font_family icon-bofang hidden group-hover:block text-[#fff] text-[24px]"></i>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderContent = () => {
    console.log('Home: renderContent called with requestId:', requestId, 'inputInfo.message:', inputInfo.message);

    // 如果有 requestId（从 URL 加载），显示 ChatView 但不传递 message
    if (requestId) {
      console.log('Home: Rendering ChatView for requestId:', requestId);
      return <ChatView inputInfo={{message: "", deepThink: false}} product={product} requestId={requestId} />;
    }

    // 如果已经有输入信息（用户输入），显示 ChatView
    if (inputInfo.message.length > 0) {
      console.log('Home: Rendering ChatView for inputInfo.message:', inputInfo.message);
      return <ChatView inputInfo={inputInfo} product={product} requestId={requestId} />;
    }

    // 否则显示主页内容
    if (inputInfo.message.length === 0) {
      console.log('Home: Rendering home page content');
      return (
        <div className="pt-[60px] flex flex-col items-center">
          <Slogn />
          <div className="w-640 rounded-xl shadow-[0_18px_39px_0_rgba(198,202,240,0.1)]">
            <GeneralInput
              placeholder={product.placeholder}
              showBtn={true}
              size="big"
              disabled={false}
              product={product}
              send={changeInputInfo}
            />
          </div>
          <div className="w-640 flex flex-wrap gap-16 mt-[16px]">
            {productList.map((item, i) => (
              <div
                key={i}
                className={`w-[22%] h-[36px] cursor-pointer flex items-center justify-center border rounded-[8px] ${item.type === product.type ? "border-[#4040ff] bg-[rgba(64,64,255,0.02)] text-[#4040ff]" : "border-[#E9E9F0] text-[#666]"}`}
                onClick={() => setProduct(item)}
              >
                <i className={`font_family ${item.img} ${item.color}`}></i>
                <div className="ml-[6px]">{item.name}</div>
              </div>
            ))}
          </div>
          <div className="mt-80 mb-120">
            <div className="text-center">
              <h2 className="text-2xl font-bold mb-2">优秀案例</h2>
              <p className="text-gray-500">和 Genie 一起提升工作效率</p>
            </div>
            <div className="flex gap-16 mt-24">
              {demoList.map((demo, i) => (
                <CaseCard key={i} {...demo} />
              ))}
            </div>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="h-full flex flex-col items-center ">
      {renderContent()}
    </div>
  );
});

Home.displayName = "Home";

export default Home;
