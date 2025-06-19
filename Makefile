# PodcastMcpGradio Makefile

.PHONY: help test local modal deploy-endpoints check-endpoints clean hf-prepare

help:
	@echo "🚀 PodcastMcpGradio - 部署命令"
	@echo ""
	@echo "📋 可用命令:"
	@echo "  make test              - 运行配置测试"
	@echo "  make local             - 启动本地模式 (需要先运行 make deploy-endpoints)"
	@echo "  make modal             - 部署到Modal模式"
	@echo "  make deploy-endpoints  - 部署GPU endpoints到Modal"
	@echo "  make check-endpoints   - 检查endpoints状态"
	@echo "  make hf-prepare        - 准备HF Spaces部署文件"
	@echo "  make clean             - 清理配置文件"
	@echo ""
	@echo "🏠 本地模式快速启动:"
	@echo "  make deploy-endpoints && make local"
	@echo ""
	@echo "☁️ Modal模式快速启动:"
	@echo "  make modal"
	@echo ""
	@echo "🤗 HF Spaces部署:"
	@echo "  make hf-prepare"

test:
	@echo "🧪 运行配置测试..."
	python src/test_deployment.py

local:
	@echo "🏠 启动本地模式..."
	@echo "💡 确保已运行 'make deploy-endpoints'"
	python start_local.py

modal:
	@echo "☁️ 部署到Modal..."
	python start_modal.py

deploy-endpoints:
	@echo "🚀 部署GPU endpoints到Modal..."
	python deployment_manager.py deploy

check-endpoints:
	@echo "🔍 检查endpoints状态..."
	python deployment_manager.py status

hf-prepare:
	@echo "🤗 准备HF Spaces部署文件..."
	@echo "✅ requirements.txt 已准备好"
	@echo "✅ app.py 入口已配置"
	@echo "📝 请阅读 README_HF.md 了解部署步骤"
	@echo ""
	@echo "📋 必需文件列表:"
	@echo "  - app.py (主入口) ✅"
	@echo "  - src/ (源代码目录) ✅"
	@echo "  - requirements.txt ✅"

clean:
	@echo "🧹 清理配置文件..."
	rm -f endpoint_config.json
	rm -rf __pycache__
	rm -rf .gradio_mcp_cache
	@echo "✅ 清理完成"

# 快捷命令
local-quick: deploy-endpoints local
modal-quick: modal
hf-quick: hf-prepare 