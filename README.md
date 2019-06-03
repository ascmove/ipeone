# Documentation

Python脚本实现东北大学网关认证、远程上线下线，适合部署在实验室内网服务器。

## Configuration

在服务器上检出项目代码，建议检出到/usr/local目录下；重命名配置文件为config-eone.ini，修改文件内基本信息、修改各个脚本内与路径相关信息。

## Usage

* 网关认证

    > python /usr/local/neu/eone.py

* 网关下线

    > python /usr/local/neu/eone.py logout
    
* 简化使用

    将neu和ineu放到/usr/bin目录下，使用vim修改里面路径信息，之后可以在bash里直接输入：
    
    > neu // 认证
    
    > ineu // 下线

## License

[MIT](http://opensource.org/licenses/MIT)


