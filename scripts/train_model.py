"""
AI 模型训练脚本

使用方法:
    python scripts/train_model.py --symbols 000001,600519 --algorithm ppo --timesteps 50000
"""

import asyncio
import argparse
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.integrations.qbot.adapter import QbotAdapter


async def train(symbols: list, algorithm: str, timesteps: int, start_date: str, end_date: str):
    """训练模型"""
    print(f"\n{'='*60}")
    print(f"AI 模型训练")
    print(f"{'='*60}")
    print(f"股票: {symbols}")
    print(f"算法: {algorithm}")
    print(f"训练步数: {timesteps}")
    print(f"数据范围: {start_date} ~ {end_date}")
    print(f"{'='*60}\n")

    # 创建适配器
    adapter = QbotAdapter(enabled=True)
    initialized = await adapter.initialize()

    if not initialized:
        print("错误: 无法初始化 Qbot 适配器")
        print("请确保已安装 torch 和 stable_baselines3:")
        print("  pip install torch stable-baselines3")
        return

    print("✓ Qbot 适配器初始化成功\n")

    # 开始训练
    print("开始训练...")
    print("(这可能需要几分钟，请耐心等待)\n")

    try:
        result = await adapter.train(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            algorithm=algorithm,
            total_timesteps=timesteps,
        )

        print(f"\n{'='*60}")
        print(f"训练完成!")
        print(f"{'='*60}")
        print(f"模型 ID: {result.model_id}")
        print(f"算法: {result.algorithm}")
        print(f"训练步数: {result.total_timesteps}")
        print(f"模型路径: {result.model_path}")
        print(f"{'='*60}\n")

        return result

    except Exception as e:
        print(f"\n训练失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def predict(symbols: list, algorithm: str):
    """使用模型预测"""
    print(f"\n{'='*60}")
    print(f"AI 模型预测")
    print(f"{'='*60}")
    print(f"股票: {symbols}")
    print(f"算法: {algorithm}")
    print(f"{'='*60}\n")

    # 创建适配器
    adapter = QbotAdapter(enabled=True)
    initialized = await adapter.initialize()

    if not initialized:
        print("错误: 无法初始化 Qbot 适配器")
        return

    print("✓ Qbot 适配器初始化成功\n")

    # 预测
    print("开始预测...\n")

    try:
        result = await adapter.predict(
            symbols=symbols,
            algorithm=algorithm,
        )

        print(f"\n{'='*60}")
        print(f"预测结果")
        print(f"{'='*60}")
        print(f"算法: {result.algorithm}")
        print(f"置信度: {result.confidence:.2%}")
        print(f"\n权重分配:")
        for symbol, weight in result.weights.items():
            print(f"  {symbol}: {weight:.2%}")
        print(f"{'='*60}\n")

        return result

    except Exception as e:
        print(f"\n预测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="AI 模型训练和预测")

    subparsers = parser.add_subparsers(dest="command", help="命令")

    # 训练命令
    train_parser = subparsers.add_parser("train", help="训练模型")
    train_parser.add_argument("--symbols", required=True, help="股票代码，逗号分隔")
    train_parser.add_argument("--algorithm", default="ppo", choices=["ppo", "a2c", "dqn", "sac"], help="算法")
    train_parser.add_argument("--timesteps", type=int, default=50000, help="训练步数")
    train_parser.add_argument("--start-date", default="2023-01-01", help="开始日期")
    train_parser.add_argument("--end-date", default="2024-12-31", help="结束日期")

    # 预测命令
    predict_parser = subparsers.add_parser("predict", help="使用模型预测")
    predict_parser.add_argument("--symbols", required=True, help="股票代码，逗号分隔")
    predict_parser.add_argument("--algorithm", default="ppo", choices=["ppo", "a2c", "dqn", "sac"], help="算法")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    symbols = args.symbols.split(",")

    if args.command == "train":
        asyncio.run(train(
            symbols=symbols,
            algorithm=args.algorithm,
            timesteps=args.timesteps,
            start_date=args.start_date,
            end_date=args.end_date,
        ))
    elif args.command == "predict":
        asyncio.run(predict(
            symbols=symbols,
            algorithm=args.algorithm,
        ))


if __name__ == "__main__":
    main()
