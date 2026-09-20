#include "capture_runner.hpp"

#include "settings.hpp"
#include "yolo_pose.hpp"
#include "yolo_session.hpp"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>

#include <opencv2/highgui.hpp>
#include <opencv2/imgproc.hpp>
#include <opencv2/videoio.hpp>

#ifdef _WIN32
#include <windows.h>
#endif

namespace fs = std::filesystem;

namespace vigia {
namespace {

bool opencv_has_gui() {
  try {
    const std::string info = cv::getBuildInformation();
    const char* markers[] = {"GTK", "Cocoa", "QT", "Win32 UI", "OpenGL"};
    for (const char* m : markers) {
      if (info.find(m) != std::string::npos) {
        return true;
      }
    }
  } catch (...) {
    return false;
  }
  return false;
}

cv::VideoCapture open_capture(const CaptureSource& source) {
  if (const auto* path = std::get_if<std::string>(&source)) {
    return cv::VideoCapture(*path);
  }
  return cv::VideoCapture(std::get<int>(source));
}

std::string exe_dir() {
#ifdef _WIN32
  wchar_t buf[MAX_PATH];
  const DWORD n = GetModuleFileNameW(nullptr, buf, MAX_PATH);
  if (n == 0 || n >= MAX_PATH) {
    return ".";
  }
  return fs::path(buf).parent_path().string();
#else
  std::error_code ec;
  auto p = fs::read_symlink("/proc/self/exe", ec);
  if (ec) {
    return ".";
  }
  return p.parent_path().string();
#endif
}

std::string find_project_root() {
  const fs::path candidates[] = {
      fs::current_path(),
      fs::path(exe_dir()),
      fs::path(exe_dir()) / "..",
      fs::path(exe_dir()) / ".." / "..",
  };
  for (const auto& base : candidates) {
    std::error_code ec;
    const fs::path root = fs::weakly_canonical(base, ec);
    if (ec) {
      continue;
    }
    if (fs::exists(root / "CMakeLists.txt") &&
        fs::exists(root / "include" / "capture_runner.hpp")) {
      return root.string();
    }
  }
  return fs::current_path().string();
}

std::string find_dotenv(const std::string& project_root) {
  const fs::path candidates[] = {
      fs::current_path() / ".env",
      fs::path(project_root) / ".env",
      fs::current_path() / "example.env",
      fs::path(project_root) / "example.env",
  };
  for (const auto& c : candidates) {
    if (fs::exists(c)) {
      return c.string();
    }
  }
  return {};
}

}  // namespace

void run_capture() {
  const std::string project_root = find_project_root();
  const std::string dotenv = find_dotenv(project_root);
  if (!dotenv.empty()) {
    load_dotenv(dotenv);
    std::cout << "Carregado " << dotenv << std::endl;
  }

  const Settings settings = Settings::from_env();
  bool show_video = settings.show_video;
  const bool show_yolo_plot = settings.show_yolo_plot;
  const bool capture_loop = settings.capture_loop;

  const std::string onnx_path = resolve_onnx_path(settings, project_root);

  YoloSession yolo(onnx_path, settings.yolo_imgsz, settings.yolo_conf);

  if (show_video && !opencv_has_gui()) {
    std::cerr << "SHOW_VIDEO=true, mas o OpenCV é headless; preview desativado." << std::endl;
    show_video = false;
  }

  cv::VideoCapture cap = open_capture(settings.capture_source);
  if (!cap.isOpened()) {
    throw std::runtime_error("Não foi possível abrir a fonte de captura (" +
                             source_label(settings.capture_source) + ")");
  }

  std::cout << "Captura iniciada: " << source_label(settings.capture_source) << std::endl;

  try {
    while (true) {
      if (show_video && (cv::waitKey(1) & 0xFF) == 'q') {
        break;
      }

      cv::Mat frame;
      if (!cap.read(frame) || frame.empty()) {
        if (is_file_source(settings.capture_source) && capture_loop) {
          cap.set(cv::CAP_PROP_POS_FRAMES, 0);
          continue;
        }
        break;
      }

      const auto poses = yolo.predict(frame);

      if (show_video) {
        cv::Mat preview = frame;
        if (show_yolo_plot) {
          preview = frame.clone();
          draw_poses(preview, poses);
        }
        cv::imshow("Preview movimentos", preview);
      }
    }
  } catch (const std::exception& e) {
    std::cerr << "Erro ao executar a captura: " << e.what() << std::endl;
    throw;
  }

  if (show_video) {
    cv::destroyAllWindows();
  }
  cap.release();
}

}  // namespace vigia
