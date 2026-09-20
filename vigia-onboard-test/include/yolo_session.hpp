#pragma once

#include "yolo_pose.hpp"

#include <memory>
#include <string>
#include <vector>

#include <opencv2/core.hpp>

namespace vigia {

class YoloSession {
 public:
  explicit YoloSession(const std::string& onnx_path, int imgsz = 320, float conf = 0.25f);
  ~YoloSession();

  YoloSession(const YoloSession&) = delete;
  YoloSession& operator=(const YoloSession&) = delete;

  std::vector<PoseDetection> predict(const cv::Mat& bgr);

  int imgsz() const { return imgsz_; }
  float conf() const { return conf_; }

 private:
  struct Impl;
  std::unique_ptr<Impl> impl_;
  int imgsz_;
  float conf_;
};

}  // namespace vigia
