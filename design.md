需求分析
1.	按照日期分类研究中涉及的文件
2.	可以在搜索知网/文献时通过截屏/上传PDF的方式保存研究涉及的文件
3.	用户可以在需要时手动输入自己的记录
4.	数据表模板
5.	Excel读取
Ps：是否需要适配像在软件开发中的git提交记录  亦或者 能自动识别源代码并找出有效更改？  

功能划分
文件结构

lib/
server/
		static/
			default_tool_config.json
			settings_template.yaml
			usertool_config_template.json
		usrdata/
			tools/
				usertool_xxx_config.json
			{项目名}/
				files/
					{日期}/
						record_meta.json
				data/
					{日期}/
						outputs/
							output_{时间戳}.json
						workflows/
							workflow_{时间戳}.json
				settings.yaml

client/

			
src/
server/
		程序文件，在server设计时补充
		DataManager/
			ToolConfigManager.py 
			
	client/
		
		
		
Server
1.	与用户对话/生成最终总结的模型
2.	解析PDF的Tool
3.	读图片的Agent
流程：
1.	接受用户输入json
a)	用户选择的文件
i.	固定路径（固定日期下的某个文件）
ii.	固定日期（从usrdata/{日期}读取文件）
b)	用户设置（用Langchain的格式化prompt）
i.	课题学科
ii.	默认prompt模板
iii.	
2.	生成处理流程并格式化prompt（高级设置：时序输入/用户选择顺序输入）
3.	用对应tool解析文件
4.	搜索记忆
5.	输入总结的llm
6.	返回json结果



Client
1.	创建（项目）lib/{项目名}/data/{日期}
2.	Setting：page 
{
default_prompt: “###默认Prompt”；
project_name: “项目name”；
required_tools:
	default_tools:
		default_tool_config.json;
	user_tools:
		usertool_xxx_config.json;(xxx用CRC32生成8位标识符来防止用户使用巨长名称导致的问题)
usertool_xxx_config.json;
}
3.	Branch界面？（时间戳 生成
4.	图形化 输入输出
5.	上传文件、图片、（语音转文字？ ->> //files   
6.	输出文件夹 （//data
7.	截屏api调用 （读取剪贴板）
8.	








实现
Server

版本控制与历史
当文件被替换或修改时，不要直接覆盖 stored_path。建议：
新文件加后缀或新 file_id 并更新 files[]（保留旧条目并在其中标注 retired_at）。
record_meta.json 中保留历史记录：history 数组或 versions 字段，便于回滚。
示例片段：
"files": [
  {"file_id":"f_old","filename":"paper.pdf","retired_at":"2025-10-12T18:00:00+08:00"},
  {"file_id":"f_new","filename":"paper_v2.pdf","uploaded_at":"2025-10-12T18:05:00+08:00"}
]



接口：
endpoint/tool
GET /tool_list ##接收tool名称返回包含所有usertool的json
GET /{user_tool} ##接收tool名称返回对应usertool的json
POST /{user_tool}/add ##接收不属于目前usertool列表的json,返回{ "code":0,## 失败时 code != 0 "status":"ok", "data":..., "message": ""##如有错误为错误说明}
POST /{user_tool}/edit ##接收属于目前usertool列表的json,返回是否成功

endpoint/project/{project}
	GET /workflow_list
POST /upload_workflow##接收workflow的json文件, 返回是否成功
	POST /start_workflow##接收workflow名称,返回id
	GET /workflow_status/{id}##接收id,返回workflow状态，前端可以参考github的workflow

endpoint/project/{project}/data
POST /{date}/upload_files 
##接收文件要放入的{date}和文件名(目前不存在),返回文件路径,cli可验证路径是否正确,server同时自动构建/更新metadata
POST /{date}/update_files 
##接收文件要放入的{date}和文件名(目前存在),返回文件路径,cli可验证路径是否正确,server同时自动更新meta（这里client会先询问用户是否覆盖原文件，若不覆盖就改用新名称upload_files）
GET /{date}/metadata





settings YAML schema:

tool_config JSON schema:

metadata JSON schema:
{
  "record_id": "20251012_163045_ab12ff34",   // 唯一记录ID（时间戳 + crc/uuid）
  "project": "project_name",
  "date": "2025-10-12",
  "created_at": "2025-10-12T16:30:45+08:00",
  "updated_at": "2025-10-12T17:01:10+08:00",
  "author": {
    "user_id": "user_123",
    "display_name": "FrozenFish"
  },
  "files": [
    {
      "file_id": "f_ab12",
      "filename": "知网论文A.pdf",
      "stored_path": "usrdata/projectA/files/2025-10-12/知网论文A_ab12.pdf",
      "original_name": "CNKI_paper_v1.pdf",
      "crc32": "ab12",
      "mime": "application/pdf",
      "size_bytes": 1048576,
      "uploaded_at": "2025-10-12T10:05:00+08:00",
      "source": "manual_upload",              // manual_upload / clipboard / screenshot / crawler
      "tags": ["文献综述", "关键文献"],
      "language": "zh",
      "status": {
        "ocr": "done",
        "parsed": "done",
        "embedding_id": "emb_12345"           // 如果做向量化检索
      },
      "notes": "含有重要结论段落3.2"
    }
  ],
  "summary": {
    "auto_summary": "usrdata/projectA/data/2025-10-12/outputs/output_20251012_170522.json",
    "user_notes": "晚上阅读讨论"
  },
  "workflows": [
    {
      "wf_id": "wf_20251012_170200",
      "name": "每日文献汇总",
      "started_at": "2025-10-12T17:02:00+08:00",
      "finished_at": "2025-10-12T17:05:22+08:00",
      "status": "success",
      "outputs": [
        "usrdata/projectA/data/2025-10-12/outputs/output_20251012_170522.json"
      ],
      "llm_model": "gpt-5-thinking-mini",
      "prompt_template": "default_prompt_v2"
    }
  ],
  "tags": ["实验日志", "10月12日"],
  "related_git": {
    "commit_hash": "2a4f6b7c",
    "repo": "git://repo/projectA"
  },
  "permissions": { "read": ["user_123"], "write": ["user_123"] },
  "notes_general": "当日会议中提到需要进一步跟进B项"
}


