#pragma once

#include <cstdint>
#include <string>
#include <variant>

namespace vigia {

using CaptureSource = std::variant<int, std::string>;

struct Settings {
  CaptureSource capture_source{0};
  bool show_video{false};
  bool show_yolo_plot{false};
  bool capture_loop{false};
  std::string yolo_model{"yolo26s-pose"};
  int yolo_imgsz{320};
  float yolo_conf{0.25f};

  static Settings from_env();
};

/** Carrega pares KEY=VALUE de um ficheiro .env para o ambiente do processo. */
void load_dotenv(const std::string& path);

/** Resolve o path do .onnx a partir de YOLO_MODEL e da raiz do projeto. */
std::string resolve_onnx_path(const Settings& settings, const std::string& project_root);

bool is_file_source(const CaptureSource& source);
std::string source_label(const CaptureSource& source);

}  // namespace vigia
