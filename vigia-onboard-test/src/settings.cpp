#include "settings.hpp"

#include <algorithm>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>

namespace fs = std::filesystem;

namespace vigia {
namespace {

std::string trim(std::string s) {
  auto not_space = [](unsigned char c) { return !std::isspace(c); };
  s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
  s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
  return s;
}

bool parse_bool(const std::string& raw) {
  std::string v = raw;
  std::transform(v.begin(), v.end(), v.begin(),
                 [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
  return v == "1" || v == "true" || v == "t" || v == "yes" || v == "y";
}

CaptureSource parse_capture_source(const std::string& raw) {
  const std::string value = trim(raw);
  if (value.empty()) {
    return 0;
  }
  bool digits = true;
  std::size_t i = 0;
  if (value[0] == '-' || value[0] == '+') {
    i = 1;
  }
  for (; i < value.size(); ++i) {
    if (!std::isdigit(static_cast<unsigned char>(value[i]))) {
      digits = false;
      break;
    }
  }
  if (digits && !value.empty() && !(value.size() == 1 && (value[0] == '-' || value[0] == '+'))) {
    return std::stoi(value);
  }
  return fs::absolute(fs::path(value).lexically_normal()).string();
}

const char* getenv_or(const char* key, const char* fallback) {
  const char* v = std::getenv(key);
  return (v && *v) ? v : fallback;
}

#ifdef _WIN32
void set_env_var(const std::string& key, const std::string& value) {
  _putenv_s(key.c_str(), value.c_str());
}
#else
void set_env_var(const std::string& key, const std::string& value) {
  setenv(key.c_str(), value.c_str(), 1);
}
#endif

}  // namespace

void load_dotenv(const std::string& path) {
  std::ifstream in(path);
  if (!in) {
    return;
  }
  std::string line;
  while (std::getline(in, line)) {
    line = trim(line);
    if (line.empty() || line[0] == '#') {
      continue;
    }
    const auto eq = line.find('=');
    if (eq == std::string::npos) {
      continue;
    }
    const std::string key = trim(line.substr(0, eq));
    std::string value = trim(line.substr(eq + 1));
    if (value.size() >= 2 &&
        ((value.front() == '"' && value.back() == '"') ||
         (value.front() == '\'' && value.back() == '\''))) {
      value = value.substr(1, value.size() - 2);
    }
    if (key.empty()) {
      continue;
    }
    // Não sobrescrever variáveis já definidas no ambiente.
    if (std::getenv(key.c_str()) == nullptr) {
      set_env_var(key, value);
    }
  }
}

Settings Settings::from_env() {
  Settings s;
  s.capture_source = parse_capture_source(getenv_or("CAPTURE_SOURCE", "0"));
  s.show_video = parse_bool(getenv_or("SHOW_VIDEO", "false"));
  s.show_yolo_plot = parse_bool(getenv_or("SHOW_YOLO_PLOT", "false"));
  s.capture_loop = parse_bool(getenv_or("CAPTURE_LOOP", "false"));
  s.yolo_model = getenv_or("YOLO_MODEL", "yolo26s-pose");
  s.yolo_imgsz = std::max(1, std::atoi(getenv_or("YOLO_IMGSZ", "320")));
  s.yolo_conf = static_cast<float>(std::atof(getenv_or("YOLO_CONF", "0.25")));
  return s;
}

std::string resolve_onnx_path(const Settings& settings, const std::string& project_root) {
  const fs::path raw(settings.yolo_model);
  if (raw.is_absolute() && fs::exists(raw)) {
    return raw.string();
  }
  if (fs::exists(raw)) {
    return fs::absolute(raw).string();
  }

  std::string stem = raw.filename().string();
  static const char* suffixes[] = {".onnx", ".pt", ".mlpackage", "_ncnn_model", ".mlmodel"};
  for (const char* suf : suffixes) {
    const std::size_t n = std::char_traits<char>::length(suf);
    if (stem.size() > n) {
      const std::string tail = stem.substr(stem.size() - n);
      std::string lower = tail;
      std::transform(lower.begin(), lower.end(), lower.begin(),
                     [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
      if (lower == suf) {
        stem = stem.substr(0, stem.size() - n);
        break;
      }
    }
  }
  if (stem.empty()) {
    stem = "yolo26s-pose";
  }

  const fs::path local = fs::path(project_root) / "models" / "yolo" / (stem + ".onnx");
  if (fs::exists(local)) {
    return local.string();
  }

  // Mesmo artefato do vigia-onboard (comparação justa).
  const fs::path sibling =
      fs::path(project_root).parent_path() / "vigia-onboard" / "vigia-capture" / "models" /
      "yolo" / (stem + ".onnx");
  if (fs::exists(sibling)) {
    return sibling.string();
  }

  throw std::runtime_error(
      "ONNX não encontrado. Exporte no vigia-capture ou defina YOLO_MODEL com path absoluto. "
      "Tentou: " +
      local.string() + " e " + sibling.string());
}

bool is_file_source(const CaptureSource& source) {
  return std::holds_alternative<std::string>(source);
}

std::string source_label(const CaptureSource& source) {
  if (const auto* path = std::get_if<std::string>(&source)) {
    return "vídeo " + *path;
  }
  return "câmera " + std::to_string(std::get<int>(source));
}

}  // namespace vigia
