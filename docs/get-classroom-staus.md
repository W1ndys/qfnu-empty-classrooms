# 获取教室状态

## 获取当前教学学期

该接口用于获取当前教学学期，学期格式为“YYYY-YYYY-X”，其中“X”表示上半年（1）或下半年（2）或小学期（3）。

请求地址：http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query

请求方法：GET

请求参数：无

响应格式：HTML

响应内容示例：

````html
<tr>
  <td>
    学期：2025-2026-1
    <!-- <select id="xnxqh" name="xnxqh" style="width:130px;" onchange="initJc(this)" >
							
						</select></td> -->
  </td>

  <td>```</td>
</tr>
````

## 查询教室状态

该接口用于查询指定教学楼在某一教学周、星期和节次的教室使用状态。
请求地址：http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query2
请求方法：POST
请求参数：

- typewhere: 固定值“jszq”
- xnxqh: 教学学期，格式为“YYYY-YYYY-X”
- jsmc_mh: 教室名称模糊查询，支持部分名称匹配，URL编码
- bjfh : 比较符号，固定值“=”
- jszt: 教室状态，固定值“8”（表示查询完全空闲的教室）
- zc: 教学周，整数
- zc2: 教学周，整数（与zc相同）
- xq: 星期，整数（1-7）
- xq2: 星期，整数（与xq相同）
- jc: 起始节次，格式为“XX”，如“01”、“02”等
- jc2: 终止节次，格式为“XX”，如“01”、“02”等（与jc相同，但节次范围必须有效，jc2大于jc）
- 其他参数请参考下方的参考请求表头

下面参考请求表头中的参数中参数未空的项可不传。

### 补充说明

教室状态与ID的对应关系

ID 1: ◆ 正常上课
ID 2: Ｊ 借用
ID 3: Ｘ 锁定
ID 4: Κ 考试
ID 5: 空闲
ID 6: Ｇ 固定调课
ID 7: Ｌ 临时调课
ID 8: 完全空闲
ID 9: M 跨模式占用

### 参考请求表头

```http
POST /jsxsd/kbxx/jsjy_query2 HTTP/1.1
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: zh-CN,zh;q=0.9
Cache-Control: no-cache
Connection: keep-alive
Content-Length: 234
Content-Type: application/x-www-form-urlencoded
Cookie: JSESSIONID=BBE16A70FF70B07E9A835512D38958A6; sto-id-20480=CBLMMCMKFAAA; JSESSIONID=695BB5B7C3A12F1B8814335CA0455D1A
Host: zhjw.qfnu.edu.cn
Origin: http://zhjw.qfnu.edu.cn
Pragma: no-cache
Referer: http://zhjw.qfnu.edu.cn/jsxsd/kbxx/jsjy_query
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36

typewhere=jszq&xnxqh=2025-2026-1&gnq_mh=&jsmc_mh=%E8%80%81%E6%96%87%E5%8F%B2%E6%A5%BC&syjs0601id=&xqbh=&jxqbh=&jslx=&jxlbh=&jsbh=&bjfh=%3D&rnrs=&jszt=8&zc=1&zc2=1&xq=1&xq2=1&jc=01&jc2=01&kbjcmsid=94786EE0ABE2D3B2E0531E64A8C09931&ssdw=

```

### 响应说明

响应格式：HTML
响应内容示例：

```html






<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">


<head id="headerid1">
	<base target='_self'>
	<title>项目列表</title>
	<meta http-equiv="pragma" content="no-cache">
	<meta http-equiv="cache-control" content="no-cache">
	<meta http-equiv="expires" content="0">
	<meta http-equiv="keywords" content="湖南强智科技教务系统">
	<meta http-equiv="description" content="湖南强智科技教务系统">
	<meta http-equiv="X-UA-Compatible" content="IE=EmulateIE8" />
<script type="text/javascript" src="/jsxsd/js/jquery-1.8.0.min.js" language="javascript" ></script>
<script type="text/javascript" src="/jsxsd/js/jquery-min.js" language="javascript" ></script>
<script type="text/javascript" src="/jsxsd/js/common.js" language="javascript" ></script>
<script type="text/javascript" src="/jsxsd/js/iepngfix_tilebg.js" language="javascript" ></script>
<script type="text/javascript" src="/jsxsd/js/easyui/jquery.easyui.min.js" language="javascript" ></script>
<script type="text/javascript" src="/jsxsd/js/jquery.autocomplete.min.js" language="javascript" ></script>
<link href="/jsxsd/framework/images/common.css" rel="stylesheet" type="text/css" />
<link href="/jsxsd/framework/images/blue.css" rel="stylesheet" type="text/css" id="link_theme" />
<link href="/jsxsd/framework/images/workstation.css" rel="stylesheet" type="text/css" />
<link href="/jsxsd/css/easyui.css" rel="stylesheet" type="text/css" />
<link href="/jsxsd/css/jquery.autocomplete.css" rel="stylesheet" type="text/css" />
</head>
<iframe id="notSession" name="notSession" style="display: none;" src=""></iframe>
<script type="text/javascript">
jQuery(document).ready(function(){
	window.setInterval(function(){
		 document.getElementById("notSession").src = "/jsxsd/framework/blankPage.jsp";
	 }, 1000 * 60 * 10);
});
</script>
<head>
<style type="">
.Nsb_r_list {
	font-size: 12px;
	color: #666;
	text-align: center
}

.Nsb_r_list a {
	color: #0C5FC0;
}

.Nsb_r_list th {
	height: 30px;
	line-height: 30px;
	font-size: 14px;
	font-weight: normal;
    color: #178fe6;
}

.Nsb_r_list th a:hover {
	text-decoration: none
}

.Nsb_r_list th span,.Nsb_r_list th a {
	display: inline-block
}
.Nsb_r_list th {
	background: #eff7fd;
	border: 1px solid #E5E5E5;
	padding: 0px;
	margin:0px;
	font-size:12px;
    color: #178fe6;
}

.Nsb_r_list td {
	border: 2px solid #E5E5E5;
/*	border-top: none;*/
	color: #000;
	padding: 5;
	margin: 0;
}

.Nsb_r_list .Nsb_r_list_thb {
	border-right: 1px solid #E5E5E5
}
.Nsb_table,.Nsb_table table {
	border-spacing: 0;
	border-collapse: separate;

}

.Nsb_table {
	width: 100%
}
</style>
</head>
<body >
<form action="/jsxsd/jspyfa/selectJx02" name="Form1" id="Form1" method="post">

		<input type="hidden" name="startZc" id="startZc" value="1" />
		<input type="hidden" name="endZc" id="endZc" value="1" />
		<input type="hidden" name="startJc" id="startJc" value="01" />
		<input type="hidden" name="endJc" id="endJc" value="01" />
		<input type="hidden" name="startXq" id="startXq" value="1" />
		<input type="hidden" name="endXq" id="endXq" value="1" />
		<input type="hidden" name="jszt" id="jszt" value="8" />
		<input type="hidden" name="xnxqh" id="xnxqh" value="2025-2026-1" />
		<input type="hidden" name="kbjcmsid" id="kbjcmsid" value="94786EE0ABE2D3B2E0531E64A8C09931" />
	<input type="hidden" name="syjs0601id" id="syjs0601id" value="" />
		<input type="hidden" id="oldrow" name="oldrow"  />
		<table id="dataList" width="100%" cellpadding="0" border="0" cellspacing="0" class="Nsb_r_list Nsb_table" >
		   <thead id="thead2" style="background-color: white;" >
	       <th align="left">

			   <input type="checkbox" name="selectAll" id="selectAll" onclick="selectAllJS(this)"  />
			   <input type="button" name="pljy" class="button el-button" value="批量借用教室" onclick="xx()" />


		   <th align="center">
			   <font color="red">双击下面表格中空白格子借用教室</font>
		   </th>

	       </th>
		<th align="right">
			教室类型
			<select name="jslx" id="jslx"  style="width:80px;" onchange="changPrentVal(3);">
				<option value="">-请选择-</option>

					<option value="01">一般教室</option>

					<option value="02">制图室</option>

					<option value="03">实验室</option>

					<option value="04">语音室</option>

					<option value="05">多媒体教室</option>

					<option value="06">多媒体授课室</option>

					<option value="07">视听教室</option>

					<option value="08">计算机房</option>

					<option value="09">网络教室</option>

					<option value="10">练功房</option>

					<option value="12">琴室</option>

					<option value="13">画室</option>

					<option value="14">办公室</option>

					<option value="15">体育馆</option>

					<option value="16">体育场</option>

					<option value="17">舞蹈房</option>

					<option value="18">游泳池</option>

					<option value="19">武术房</option>

					<option value="20">篮排馆</option>

					<option value="21">足球场</option>

					<option value="22">体操房</option>

					<option value="23">网球场</option>

					<option value="24">跆拳道馆</option>

					<option value="25">健身房</option>

					<option value="26">乒乓球馆</option>

					<option value="27">羽毛球馆</option>

					<option value="28">田径场</option>

					<option value="31">武术场地</option>

					<option value="32">体育舞蹈教室</option>

					<option value="33">琴房</option>

					<option value="34">体院舞蹈教室</option>

					<option value="35">体院体操房</option>

					<option value="36">体院篮球馆</option>

					<option value="37">体院瑜伽教室</option>

					<option value="38">排球场地</option>

					<option value="39">乒乓球场地</option>

					<option value="40">体院武术馆</option>

					<option value="41">足球场地</option>

					<option value="42">录播教室</option>

					<option value="43">健美操场地</option>

					<option value="44">羽毛球场地</option>

					<option value="45">机房</option>

					<option value="46">体院琴房</option>

					<option value="47">手球场地</option>

					<option value="48">体院足球场</option>

					<option value="49">体院乒乓球室</option>

					<option value="50">普通非多媒体教室</option>

					<option value="51">网球场地</option>

					<option value="52">体院排球馆</option>

					<option value="53">篮球场地</option>

					<option value="54">体院健美操教室</option>

					<option value="55">体院棋牌室</option>

					<option value="56">田径场地</option>

					<option value="57">体院田径场</option>

					<option value="58">语音教室</option>

					<option value="59">瑜伽场地</option>

					<option value="60">保健课场地</option>

			</select>
		    功能区名称<input type="text" name="gnq_mh" id="gnq_mh" value="" style="width:80px;" onchange="changPrentVal(1);"/>
	         教室名称<input type="text" name="jsmc_mh" id="jsmc_mh" value="" style="width:80px;" onchange="changPrentVal(2);"/>
	        <input type="button"  value="查 询" class="button el-button" onclick="queryKb_mh();" />
		</th>
	   </thead>
		</table>

	<table id="dataList" width="100%" cellpadding="0" class="Nsb_r_list Nsb_table" >

		<thead id="thead1" style="background-color: white;

			" >
		<th width="180" height="160" class="Nsb_r_list_thb" scope="col">星期</th>


            <th class="Nsb_r_list_thb" colspan="1" scope="col">星期一</th>

		</tr>
		<tr height="60">
			<td>
			</td>



						<td id="jc0" tdvalue="0102" tdKssj="08:00" tdJssj="09:50">01<br>02<br></td>




		</tr>
		</thead>

		<tr  onMouseOver="this.style.cursor='hand'" jsbh="1306" onclick="clickTr(this,'1')">
		<td width="180">
			<input type="checkbox" value="1306" name="jsids"  /> 老文史楼101(75/30)
		</td>


			<td width="18" height="11" align="center" ondblclick="clickTd(this)" onmousemove="showJc1(this)"></td>



		</tr>

		<tr  onMouseOver="this.style.cursor='hand'" jsbh="0266" onclick="clickTr(this,'2')">
		<td width="180">
			<input type="checkbox" value="0266" name="jsids"  /> 老文史楼106(31/10)
		</td>


			<td width="18" height="11" align="center" ondblclick="clickTd(this)" onmousemove="showJc1(this)"></td>



		</tr>

		<tr  onMouseOver="this.style.cursor='hand'" jsbh="1311" onclick="clickTr(this,'3')">
		<td width="180">
			<input type="checkbox" value="1311" name="jsids"  /> 老文史楼107(75/30)
		</td>


			<td width="18" height="11" align="center" ondblclick="clickTd(this)" onmousemove="showJc1(this)"></td>



		</tr>

		<tr  onMouseOver="this.style.cursor='hand'" jsbh="1314" onclick="clickTr(this,'4')">
		<td width="180">
			<input type="checkbox" value="1314" name="jsids"  /> 老文史楼108(40/0)
		</td>


			<td width="18" height="11" align="center" ondblclick="clickTd(this)" onmousemove="showJc1(this)"></td>



		</tr>

		<tr  onMouseOver="this.style.cursor='hand'" jsbh="1318" onclick="clickTr(this,'5')">
		<td width="180">
			<input type="checkbox" value="1318" name="jsids"  /> 老文史楼109(75/30)
		</td>


			<td width="18" height="11" align="center" ondblclick="clickTd(this)" onmousemove="showJc1(this)"></td>



		</tr>



	</table>
</form>
<!-- 以下内容无参考价值，已删除省略 -->
</body>
</html>
```

## 解析说明

1. 发送POST请求到指定的接口地址，携带必要的请求参数。
2. 解析响应内容，提取表格中所有教室名称，由于状态已经在查询参数中指定为“完全空闲”，因此所有返回的教室均为空闲状态。注意表格中的教室名称格式为“教室名称(容量/已用人数)”。解析结果需要去掉括号及其内容，只保留教室名称部分。
3. 返回解析结果。
