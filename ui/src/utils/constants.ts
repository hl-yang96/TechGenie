/**
 * 预览状态的tab选项
*/
import csvIcon from '@/assets/icon/CSV.png';
import docxIcon from '@/assets/icon/docx.png';
import excleIcon from '@/assets/icon/excle.png';
import pdfIcon from '@/assets/icon/pdf.png';
import txtIcon from '@/assets/icon/txt.png';
import htmlIcon  from '@/assets/icon/HTML.png';
import demo3 from '@/assets/icon/demo3.png';
import demo4 from '@/assets/icon/demo4.png';
import fodInterviewImg from '../../../docs/img/fod_interview_questions.jpg';
import techCoachImg from '../../../docs/img/TechCoach_Analyze.jpg';

import { ActionViewItemEnum } from "./enums";

export const iconType:Record<string, string> = {
  doc: docxIcon,
  docx: docxIcon,
  xlsx: excleIcon,
  csv: csvIcon,
  pdf: pdfIcon,
  txt: txtIcon,
  html: htmlIcon,
};

export const actionViewOptions = [
  {
    label: '实时跟随',
    value: ActionViewItemEnum.follow,
    split: false
  },
  {
    label: '浏览器',
    value: ActionViewItemEnum.browser,
  },
  {
    label: '文件',
    value: ActionViewItemEnum.file
  }
];

export const defaultActiveActionView = actionViewOptions[0].value;

export const productList = [{
  name: '网页模式',
  img: 'icon-diannao',
  type: 'html',
  placeholder: 'Genie会完成你的任务并以HTML网页方式输出报告',
  color: 'text-[#29CC29]'
},
{
  name: '文档模式',
  img: 'icon-wendang',
  type: 'docs',
  placeholder: 'Genie会完成你的任务并以markdown格式输出文档',
  color: 'text-[#4040FF]'
},
{
  name: 'PPT模式',
  img: 'icon-ppt',
  type: 'ppt',
  placeholder: 'Genie会完成你的任务并以PPT方式输出结论',
  color: 'text-[#FF860D]'
},
{
  name: '表格模式',
  img: 'icon-biaoge',
  type: 'table',
  placeholder: 'Genie会完成你的任务并以表格格式输出结论',
  color: 'text-[#FF3333]'
}];

export const defaultProduct = productList[0];

export const RESULT_TYPES = ['task_summary', 'result'];

export const InputSize:Record<string, string>  = {
  big: '106',
  medium: '72',
  small: '32'
};

export const demoList = [
  {
    title: '个人项目面试题分析',
    description: '请基于我的项目经历：流式缓存更新服务，为我生成一些面试中可能遇到的面试题。',
    tag: '面试准备',
    url: '/docs/project_interview_question.md',
    image: fodInterviewImg
  },
  {
    title: '代码库技术分析报告',
    description: '请为我分析 TechCoach 这个 AI Agent 项目，并且生成一份详细的技术报告。',
    tag: '项目分析',
    url: '/docs/TechCoach_tech_report.html',
    image: techCoachImg
  },
  {
    title: '个性化面试准备策略报告',
    description: '基于我的个人情况，告诉我操作系统应该如何复习？',
    tag: '学习指导',
    url: '/docs/OS_preparation_report.html',
    image: demo3
  },
  {
    title: '个人简历项目经历指导',
    description: '基于我的这个项目，我应该在简历中如何体现出我的亮点？',
    tag: '简历优化',
    url: '/docs/project_analyze_for_resume.md',
    image: demo4
  }
];
