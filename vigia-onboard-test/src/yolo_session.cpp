#include "yolo_session.hpp"

#include "yolo_pose.hpp"

#include <array>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include <onnxruntime_cxx_api.h>

#ifdef _WIN32
#include <windows.h>
#endif

namespace vigia {
namespace {

#ifdef _WIN32
std::wstring utf8_to_wide(const std::string& utf8) {
  if (utf8.empty()) {
    return {};
  }
  const int size = MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), -1, nullptr, 0);
  std::wstring wide(static_cast<std::size_t>(size), L'\0');
  MultiByteToWideChar(CP_UTF8, 0, utf8.c_str(), -1, wide.data(), size);
  if (!wide.empty() && wide.back() == L'\0') {
    wide.pop_back();
  }
  return wide;
}
#endif

}  // namespace

struct YoloSession::Impl {
  Ort::Env env{ORT_LOGGING_LEVEL_WARNING, "vigia-capture-cpp"};
  Ort::SessionOptions options;
  std::unique_ptr<Ort::Session> session;
  Ort::AllocatorWithDefaultOptions allocator;
  std::string input_name;
  std::string output_name;
  std::vector<int64_t> input_shape;
  std::vector<int64_t> output_shape;
};

YoloSession::YoloSession(const std::string& onnx_path, int imgsz, float conf)
    : impl_(std::make_unique<Impl>()), imgsz_(imgsz), conf_(conf) {
  impl_->options.SetIntraOpNumThreads(0);  // deixa o ORT escolher
  impl_->options.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_ENABLE_ALL);

#ifdef _WIN32
  const std::wstring wide_path = utf8_to_wide(onnx_path);
  impl_->session =
      std::make_unique<Ort::Session>(impl_->env, wide_path.c_str(), impl_->options);
#else
  impl_->session =
      std::make_unique<Ort::Session>(impl_->env, onnx_path.c_str(), impl_->options);
#endif

  {
    auto name = impl_->session->GetInputNameAllocated(0, impl_->allocator);
    impl_->input_name = name.get();
  }
  {
    auto name = impl_->session->GetOutputNameAllocated(0, impl_->allocator);
    impl_->output_name = name.get();
  }

  auto in_info = impl_->session->GetInputTypeInfo(0).GetTensorTypeAndShapeInfo();
  impl_->input_shape = in_info.GetShape();
  auto out_info = impl_->session->GetOutputTypeInfo(0).GetTensorTypeAndShapeInfo();
  impl_->output_shape = out_info.GetShape();

  // Preferir imgsz do artefato quando fixo (ex.: [1,3,320,320]).
  if (impl_->input_shape.size() >= 4 && impl_->input_shape[2] > 0) {
    imgsz_ = static_cast<int>(impl_->input_shape[2]);
  }

  std::cout << "YOLO ONNX carregado: " << onnx_path << " imgsz=" << imgsz_
            << " in=" << impl_->input_name << " out=" << impl_->output_name << std::endl;
}

YoloSession::~YoloSession() = default;

std::vector<PoseDetection> YoloSession::predict(const cv::Mat& bgr) {
  LetterboxMeta meta;
  cv::Mat blob = letterbox(bgr, imgsz_, meta);

  std::array<int64_t, 4> shape{1, 3, imgsz_, imgsz_};
  Ort::MemoryInfo mem = Ort::MemoryInfo::CreateCpu(OrtArenaAllocator, OrtMemTypeDefault);
  Ort::Value input_tensor = Ort::Value::CreateTensor<float>(
      mem, blob.ptr<float>(), static_cast<size_t>(blob.total()), shape.data(), shape.size());

  const char* input_names[] = {impl_->input_name.c_str()};
  const char* output_names[] = {impl_->output_name.c_str()};

  auto outputs =
      impl_->session->Run(Ort::RunOptions{nullptr}, input_names, &input_tensor, 1, output_names, 1);

  float* out_data = outputs[0].GetTensorMutableData<float>();
  auto out_shape = outputs[0].GetTensorTypeAndShapeInfo().GetShape();
  // Esperado [1, 300, 57] (end2end Ultralytics pose).
  if (out_shape.size() != 3) {
    throw std::runtime_error("Formato de saída ONNX inesperado (esperado rank 3).");
  }
  const int max_det = static_cast<int>(out_shape[1]);
  const int stride = static_cast<int>(out_shape[2]);
  return decode_pose_output(out_data, max_det, stride, conf_, meta);
}

}  // namespace vigia
