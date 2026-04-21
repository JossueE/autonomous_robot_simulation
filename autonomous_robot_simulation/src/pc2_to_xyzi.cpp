/*
@description:
In order to obtain a correct information message from ignition lidar data,
this node converts PointCloud2 messages to PCL PointXYZI format and back to PointCloud2.
This is necessary because ignition lidar data comes in a format that is not directly compatible
with standard PCL processing pipelines. That are used by Fast-LIO2 and other SLAM algorithms.
*/
#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/point_cloud2.hpp>
#include <pcl/point_cloud.h>
#include <pcl/point_types.h>

#include <pcl_conversions/pcl_conversions.h>
#include <pcl_conversions.hpp>  // helper de conversiones

class Pc2ToXYZI : public rclcpp::Node {
  private:

    std::string lidar_topic_in_;
    std::string lidar_topic_out_;
    std::string lidar_frame_id_;

    rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr sub;
    rclcpp::Publisher<sensor_msgs::msg::PointCloud2>::SharedPtr pub;

  public:

    Pc2ToXYZI() : Node("pc2_to_xyzi") {

      this->declare_parameter("lidar_topic_in_", std::string("/lidar/points_ign"));
      this->declare_parameter("lidar_topic_out_", std::string("/lidar/points_pcl"));
      this->declare_parameter("lidar_frame_id_", std::string("lidar_link"));

      this->get_parameter("lidar_topic_in_", lidar_topic_in_);
      this->get_parameter("lidar_topic_out_", lidar_topic_out_);
      this->get_parameter("lidar_frame_id_", lidar_frame_id_);

      sub = create_subscription<sensor_msgs::msg::PointCloud2>(lidar_topic_in_, rclcpp::SensorDataQoS(),
        [this](const sensor_msgs::msg::PointCloud2::ConstSharedPtr msg){
          pcl::PointCloud<pcl::PointXYZI> cloud;
          pcl_df::fromROSMsg(*msg, cloud);                // ← convert to PCL (XYZI)
          sensor_msgs::msg::PointCloud2 out;
          pcl::toROSMsg(cloud, out);                   // ← return to PointCloud2
          out.header = msg->header;                    // mantein frame y stamp
          out.header.frame_id = lidar_frame_id_;
          pub->publish(out);
        });

      pub = create_publisher<sensor_msgs::msg::PointCloud2>(lidar_topic_out_, rclcpp::SensorDataQoS());
    }

    ~Pc2ToXYZI() //Class destructor definition
    {
      RCLCPP_INFO(this->get_logger(), "Node Pc2ToXYZI has been terminated"); 
    }
};

int main(int argc, char** argv){
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<Pc2ToXYZI>());
  rclcpp::shutdown();
  return 0;
}

