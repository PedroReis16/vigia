#include "yolo_pose.hpp"

#include <algorithm>
#include <cmath>
#include <cstring>

#include <opencv2/imgproc.hpp>

namespace vigia {
namespace {

// COCO-17 skeleton (0-indexed pairs).
const int kSkeleton[][2] = {
    {15, 13}, {13, 11}, {16, 14}, {14, 12}, {11, 12}, {5, 11}, {6, 12},
    {5, 6},   {5, 7},   {6, 8},   {7, 9},   {8, 10},  {1, 2},  {0, 1},
    {0, 2},   {1, 3},   {2, 4},   {3, 5},   {4, 6},
};

}  // namespace

cv::Mat letterbox(const cv::Mat& bgr, int imgsz, LetterboxMeta& meta) {
  meta.orig_w = bgr.cols;
  meta.orig_h = bgr.rows;
  meta.imgsz = imgsz;

  const float r =
      std::min(static_cast<float>(imgsz) / bgr.cols, static_cast<float>(imgsz) / bgr.rows);
  meta.scale = r;
  const int new_w = static_cast<int>(std::round(bgr.cols * r));
  const int new_h = static_cast<int>(std::round(bgr.rows * r));
  meta.pad_x = (imgsz - new_w) * 0.5f;
  meta.pad_y = (imgsz - new_h) * 0.5f;

  cv::Mat resized;
  cv::resize(bgr, resized, cv::Size(new_w, new_h), 0, 0, cv::INTER_LINEAR);

  cv::Mat padded(imgsz, imgsz, CV_8UC3, cv::Scalar(114, 114, 114));
  const int left = static_cast<int>(std::round(meta.pad_x - 0.1f));
  const int top = static_cast<int>(std::round(meta.pad_y - 0.1f));
  resized.copyTo(padded(cv::Rect(left, top, new_w, new_h)));

  cv::Mat rgb;
  cv::cvtColor(padded, rgb, cv::COLOR_BGR2RGB);
  rgb.convertTo(rgb, CV_32F, 1.0 / 255.0);

  // HWC → CHW contiguous blob for ORT
  std::vector<cv::Mat> channels(3);
  cv::split(rgb, channels);
  cv::Mat blob(1, 3 * imgsz * imgsz, CV_32F);
  float* dst = blob.ptr<float>();
  for (int c = 0; c < 3; ++c) {
    std::memcpy(dst + c * imgsz * imgsz, channels[c].ptr<float>(),
                static_cast<std::size_t>(imgsz * imgsz) * sizeof(float));
  }
  return blob;
}

std::vector<PoseDetection> decode_pose_output(const float* data, int max_det, int stride,
                                              float conf_thres, const LetterboxMeta& meta) {
  std::vector<PoseDetection> out;
  out.reserve(32);

  const float inv_scale = (meta.scale > 0.f) ? (1.f / meta.scale) : 1.f;

  auto map_x = [&](float x) {
    return (x - meta.pad_x) * inv_scale;
  };
  auto map_y = [&](float y) {
    return (y - meta.pad_y) * inv_scale;
  };

  for (int i = 0; i < max_det; ++i) {
    const float* row = data + i * stride;
    const float conf = row[4];
    if (conf < conf_thres) {
      continue;
    }

    PoseDetection det;
    det.conf = conf;
    float x1 = map_x(row[0]);
    float y1 = map_y(row[1]);
    float x2 = map_x(row[2]);
    float y2 = map_y(row[3]);
    x1 = std::clamp(x1, 0.f, static_cast<float>(meta.orig_w - 1));
    y1 = std::clamp(y1, 0.f, static_cast<float>(meta.orig_h - 1));
    x2 = std::clamp(x2, 0.f, static_cast<float>(meta.orig_w - 1));
    y2 = std::clamp(y2, 0.f, static_cast<float>(meta.orig_h - 1));
    det.box = cv::Rect2f(cv::Point2f(x1, y1), cv::Point2f(x2, y2));

    det.keypoints.resize(17);
    for (int k = 0; k < 17; ++k) {
      const float* kp = row + 6 + k * 3;
      det.keypoints[k].x = map_x(kp[0]);
      det.keypoints[k].y = map_y(kp[1]);
      det.keypoints[k].conf = kp[2];
    }
    out.push_back(std::move(det));
  }
  return out;
}

void draw_poses(cv::Mat& bgr, const std::vector<PoseDetection>& poses, float kpt_conf) {
  for (const auto& pose : poses) {
    const cv::Rect box(pose.box);
    cv::rectangle(bgr, box, cv::Scalar(0, 200, 80), 2);
    const std::string label = cv::format("%.2f", pose.conf);
    cv::putText(bgr, label, cv::Point(box.x, std::max(0, box.y - 4)), cv::FONT_HERSHEY_SIMPLEX,
                0.5, cv::Scalar(0, 200, 80), 1, cv::LINE_AA);

    if (pose.keypoints.size() < 17) {
      continue;
    }

    for (const auto& edge : kSkeleton) {
      const auto& a = pose.keypoints[edge[0]];
      const auto& b = pose.keypoints[edge[1]];
      if (a.conf < kpt_conf || b.conf < kpt_conf) {
        continue;
      }
      cv::line(bgr, cv::Point(static_cast<int>(a.x), static_cast<int>(a.y)),
               cv::Point(static_cast<int>(b.x), static_cast<int>(b.y)), cv::Scalar(255, 128, 0), 2,
               cv::LINE_AA);
    }
    for (const auto& kp : pose.keypoints) {
      if (kp.conf < kpt_conf) {
        continue;
      }
      cv::circle(bgr, cv::Point(static_cast<int>(kp.x), static_cast<int>(kp.y)), 3,
                 cv::Scalar(0, 0, 255), -1, cv::LINE_AA);
    }
  }
}

}  // namespace vigia
