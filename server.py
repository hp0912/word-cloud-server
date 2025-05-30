import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from utils import gen_word_cloud_pic
from loguru import logger

class WordCloudHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # 解析URL路径
        parsed_path = urlparse(self.path)
        
        # 检查是否是目标接口
        if parsed_path.path != '/api/v1/word-cloud/gen':
            self.send_error(404, "Not Found")
            return
        
        try:
            # 获取请求体长度
            content_length = int(self.headers.get('Content-Length', 0))
            
            # 读取请求体
            post_data = self.rfile.read(content_length)
            
            # 解析JSON数据
            request_data = json.loads(post_data.decode('utf-8'))
            
            # 提取参数
            content = request_data.get('content', '')
            chat_room_id = request_data.get('chat_room_id', '')
            mode = request_data.get('mode', 'yesterday')
            
            # 参数验证
            if not content or not chat_room_id:
                self.send_error(400, "Missing required parameters: content and chat_room_id")
                return
            
            if mode not in ['yesterday', 'week', 'month', 'year']:
                self.send_error(400, "Invalid mode. Must be one of: yesterday, week, month, year")
                return
            
            logger.info(f"Generating word cloud for chat_room_id: {chat_room_id}, mode: {mode}")
            
            # 调用词云生成函数
            gen_word_cloud_pic(content, chat_room_id, mode)
            
            # 生成文件路径
            import datetime
            _now = datetime.datetime.now()
            _date = ""
            if mode == 'yesterday':
                _date = (_now + datetime.timedelta(days=-1)).strftime("%Y%m%d")
            elif mode == 'week':
                _week = _now.isocalendar()
                _date = "{}{}".format(_week[0], _week[1] - 1)
            elif mode == 'month':
                _now = _now.replace(day=1)
                _date = (_now + datetime.timedelta(days=-1)).strftime("%Y%m")
            elif mode == 'year':
                _date = _now.year - 1
            
            output_filename = f"/app/wordcloud/{_date}_{chat_room_id}.png"
            
            # 检查文件是否存在
            if not os.path.exists(output_filename):
                self.send_error(500, "Failed to generate word cloud image")
                return
            
            # 读取生成的图片文件
            with open(output_filename, 'rb') as f:
                image_data = f.read()
            
            # 发送响应头
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(image_data)))
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(output_filename)}"')
            self.end_headers()
            
            # 发送图片数据
            self.wfile.write(image_data)
            
            logger.success(f"Word cloud image sent successfully for chat_room_id: {chat_room_id}")
            
        except json.JSONDecodeError:
            self.send_error(400, "Invalid JSON format")
        except Exception as e:
            logger.error(f"Error generating word cloud: {str(e)}")
            self.send_error(500, f"Internal server error: {str(e)}")
    
    def do_GET(self):
        # 对于GET请求，返回API说明
        if self.path == '/':
            response = {
                "message": "Word Cloud API Server",
                "version": "1.0",
                "endpoints": {
                    "POST /api/v1/word-cloud/gen": {
                        "description": "Generate word cloud image",
                        "parameters": {
                            "content": "string (required) - Text content for word cloud",
                            "chat_room_id": "string (required) - Chat room identifier",
                            "mode": "string (optional) - Time mode: yesterday, week, month, year (default: yesterday)"
                        },
                        "returns": "PNG image file"
                    }
                }
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response, indent=2, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_error(404, "Not Found")
    
    def log_message(self, format, *args):
        # 使用loguru记录日志
        logger.info(f"{self.client_address[0]} - {format % args}")

def run_server(port=9000):
    """启动HTTP服务器"""
    # 确保输出目录存在
    os.makedirs('/app/wordcloud', exist_ok=True)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, WordCloudHandler)
    
    logger.info(f"Word Cloud Server starting on port {port}")
    logger.info(f"API endpoint: POST http://localhost:{port}/api/v1/word-cloud/gen")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        httpd.shutdown()

if __name__ == '__main__':
    run_server()