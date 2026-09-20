#pragma once

#include <opencv2/core.hpp>
#include <vector>

namespace vigia {

struct Keypoint {
  float x{0.f};
  float y{0.f};
  float conf{0.f};
};

struct PoseDetection {
  cv::Rect2f box;  // xyxy no espaço da imagem original
  float conf{0.f};
  std::vector<Keypoint> keypoints;  // 17 COCO
};

struct LetterboxMeta {
  float scale{1.f};
  float pad_x{0.f};
  float pad_y{0.f};
  int orig_w{0};
  int orig_h{0};
  int imgsz{320};
};

/** Letterbox BGR → NCHW float32 [0,1], tamanho imgsz×imgsz. */
cv::Mat letterbox(const cv::Mat& bgr, int imgsz, LetterboxMeta& meta);

/**
 * Decode saída end2end Ultralytics pose: [1, 300, 57]
 * = xyxy + conf + cls + 17*(x,y,conf) no espaço letterbox.
 */
std::vector<PoseDetection> decode_pose_output(const float* data, int max_det, int stride,
                                              float conf_thres, const LetterboxMeta& meta);

void draw_poses(cv::Mat& bgr, const std::vector<PoseDetection>& poses, float kpt_conf = 0.5f);

}  // namespace vigia
