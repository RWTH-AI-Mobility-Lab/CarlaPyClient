"""
摄像头性能测试脚本

用于测试新的多线程队列方案的性能表现。
"""
import time
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from carla_bike_sim.carla.carla_client_manager import CarlaClientManager


def test_camera_performance():
    """测试摄像头性能"""
    app = QApplication(sys.argv)

    # 连接到CARLA服务器
    print("正在连接到CARLA服务器...")
    carla_manager = CarlaClientManager(host='localhost', port=2000)

    if not carla_manager.connect():
        print("❌ 连接CARLA服务器失败")
        return

    print("✓ 已连接到CARLA服务器")

    # 启动仿真
    print("\n正在启动仿真...")
    if not carla_manager.start_simulation(vehicle_blueprint="vehicle.bh.crossbike"):
        print("❌ 启动仿真失败")
        carla_manager.disconnect()
        return

    print("✓ 仿真已启动")
    print("\n开始收集性能数据（10秒）...")

    # 记录初始状态
    initial_stats = carla_manager.sensor_manager.get_performance_stats()
    print(f"\n初始状态:")
    for camera, stats in initial_stats.items():
        print(f"  {camera}: 队列大小={stats['queue_size']}, 丢帧数={stats['dropped_frames']}")

    # 等待10秒收集数据
    start_time = time.time()
    frame_counts = {camera: 0 for camera in ['front', 'rear', 'left', 'right']}

    def count_frame(camera_name):
        def counter(image):
            frame_counts[camera_name] += 1
        return counter

    # 连接信号统计帧数
    carla_manager.sensor_manager.front_camera_image_ready.connect(
        count_frame('front')
    )
    carla_manager.sensor_manager.rear_camera_image_ready.connect(
        count_frame('rear')
    )
    carla_manager.sensor_manager.left_camera_image_ready.connect(
        count_frame('left')
    )
    carla_manager.sensor_manager.right_camera_image_ready.connect(
        count_frame('right')
    )

    # 定时检查性能
    def check_performance():
        elapsed = time.time() - start_time
        if elapsed >= 10:
            timer.stop()

            # 输出最终统计
            final_stats = carla_manager.sensor_manager.get_performance_stats()
            print(f"\n最终状态（运行{elapsed:.1f}秒）:")

            total_frames = 0
            total_dropped = 0

            for camera in ['front', 'rear', 'left', 'right']:
                stats = final_stats[camera]
                frames = frame_counts[camera]
                total_frames += frames
                total_dropped += stats['dropped_frames']

                fps = frames / elapsed if elapsed > 0 else 0
                print(f"  {camera}:")
                print(f"    - 接收帧数: {frames} ({fps:.1f} FPS)")
                print(f"    - 当前队列: {stats['queue_size']}")
                print(f"    - 丢弃帧数: {stats['dropped_frames']}")

            print(f"\n总计:")
            print(f"  - 总接收帧数: {total_frames}")
            print(f"  - 总丢弃帧数: {total_dropped}")
            print(f"  - 平均FPS: {total_frames / (4 * elapsed):.1f}")

            if total_dropped > 0:
                loss_rate = (total_dropped / (total_frames + total_dropped)) * 100
                print(f"  - 丢帧率: {loss_rate:.2f}%")
                print(f"\n⚠️  检测到丢帧，可能需要增加队列大小或优化处理速度")
            else:
                print(f"  - 丢帧率: 0.00%")
                print(f"\n✓ 性能良好，无丢帧")

            # 清理
            print("\n正在停止仿真...")
            carla_manager.stop_simulation()
            carla_manager.disconnect()
            print("✓ 测试完成")

            app.quit()
        else:
            # 每秒打印一次进度
            if int(elapsed) % 1 == 0:
                current_stats = carla_manager.sensor_manager.get_performance_stats()
                current_fps = sum(frame_counts.values()) / elapsed if elapsed > 0 else 0
                print(f"  [{int(elapsed)}s] 当前平均FPS: {current_fps:.1f}, "
                      f"队列: {[s['queue_size'] for s in current_stats.values()]}, "
                      f"丢帧: {sum(s['dropped_frames'] for s in current_stats.values())}")

    timer = QTimer()
    timer.timeout.connect(check_performance)
    timer.start(100)  # 每100ms检查一次

    # 运行Qt事件循环
    sys.exit(app.exec())


if __name__ == '__main__':
    print("=" * 60)
    print("CARLA 摄像头性能测试")
    print("=" * 60)
    print("\n此测试将:")
    print("1. 连接到CARLA服务器")
    print("2. 启动仿真并创建自行车")
    print("3. 收集10秒的摄像头性能数据")
    print("4. 输出帧率、队列状态和丢帧统计")
    print("\n请确保CARLA服务器正在运行...")
    print("\n" + "=" * 60 + "\n")

    try:
        test_camera_performance()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试出错: {e}")
        import traceback
        traceback.print_exc()
