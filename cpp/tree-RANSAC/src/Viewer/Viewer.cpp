#include <Magnum/GL/DefaultFramebuffer.h>
#include <Magnum/Platform/Sdl2Application.h>
#include <Magnum/ImGuiIntegration/Context.hpp>

#include <Corrade/Utility/DebugStl.h>

#include <Magnum/GL/Context.h>
#include <Magnum/GL/Renderer.h>
#include <Magnum/GL/Version.h>
#include <Magnum/GL/Buffer.h>
#include <Magnum/GL/Mesh.h>
#include <Magnum/GL/Texture.h>
#include <Magnum/GL/TextureFormat.h>

#include <Magnum/Image.h>
#include <Magnum/ImageView.h>
#include <Magnum/PixelFormat.h>

#include <Magnum/Math/Color.h>
#include <Magnum/Math/Matrix4.h>
#include <Magnum/Math/Vector3.h>

#include <Corrade/Containers/ArrayViewStl.h>
#include <Corrade/Containers/StridedArrayView.h>
#include <Corrade/Containers/Array.h>
#include <Corrade/Containers/Optional.h>

#include <Magnum/SceneGraph/Camera.h>
#include <Magnum/SceneGraph/Drawable.h>
#include <Magnum/SceneGraph/MatrixTransformation3D.h>
#include <Magnum/SceneGraph/Object.h>
#include <Magnum/SceneGraph/Scene.h>

#include <random>
#include <map>
#include <limits>

#include "PointShader.h"
#include "ArcBall.h"
#include "ArcBallCamera.h"

#include "../TreeDetector.h"

using namespace Magnum;
using namespace Magnum::Examples;
using namespace Math::Literals;
using Object3D = SceneGraph::Object<SceneGraph::MatrixTransformation3D>;
using Scene3D = SceneGraph::Scene<SceneGraph::MatrixTransformation3D>;

int runViewer(TreeDetector& detector, int argc, char** argv);

// set the number of colors in the colormap
const int CMAP_SIZE=512;

// Helper struct for bounding box computation from a set of points
struct BBox {
    double x_min = std::numeric_limits<double>::max();
    double y_min = std::numeric_limits<double>::max();
    double z_min = std::numeric_limits<double>::max();
    double x_max = -std::numeric_limits<double>::max();
    double y_max = -std::numeric_limits<double>::max();
    double z_max = -std::numeric_limits<double>::max();

    BBox(const std::vector<TreeDetector::Point>& points) {
        for (const auto& p : points) {
            add_point(p);
        }
    }

    void add_point(const double3& p) {
        x_min = std::min(x_min, p.x);
        y_min = std::min(y_min, p.y);
        z_min = std::min(z_min, p.z);
        x_max = std::max(x_max, p.x);
        y_max = std::max(y_max, p.y);
        z_max = std::max(z_max, p.z);
    }

    double3 center() {
        return {
            x_min + (x_max-x_min)/2,
            y_min + (y_max-y_min)/2,
            z_min + (z_max-z_min)/2
        };
    }

    double3 size() {
        return {
            (x_max-x_min),
            (y_max-y_min),
            (z_max-z_min)
        };
    }
};

class Viewer: public Platform::Application {
    public:
        explicit Viewer(const Arguments& arguments, TreeDetector& detector);
    
    private:
        void drawEvent() override;

        void viewportEvent(ViewportEvent& event) override;
        void keyPressEvent(KeyEvent& event) override;
        void keyReleaseEvent(KeyEvent& event) override;
        void mousePressEvent(MouseEvent& event) override;
        void mouseReleaseEvent(MouseEvent& event) override;
        void mouseMoveEvent(MouseMoveEvent& event) override;
        void mouseScrollEvent(MouseScrollEvent& event) override;
        void textInputEvent(TextInputEvent& event) override;

        void updateColormap();
        void randomiseColormap();

        ImGuiIntegration::Context _imgui{NoCreate};
        GL::Mesh _mesh;
        PointShader _shader;
        GL::Buffer _vertexBuffer, _labelBuffer;

        Containers::Array<float> _colormap{3*CMAP_SIZE};
        GL::Texture1D _texture;

        Scene3D _scene;
        SceneGraph::DrawableGroup3D _drawables;
        Containers::Optional<ArcBallCamera> _arcballCamera;

        Color4 _clearColor = 0x222222ff_rgbaf;
        float _pointSize = 2.0f;

        TreeDetector& _detector;
        std::map<int,int> _segments;
};

class VisualizationDrawable: public SceneGraph::Drawable3D {
    public:
        explicit VisualizationDrawable(Object3D& object,
            PointShader& shader, GL::Mesh& mesh,
            SceneGraph::DrawableGroup3D& drawables):
                SceneGraph::Drawable3D{object, &drawables}, _shader(shader),
                _mesh(mesh) {}

        void draw(const Matrix4& transformation, SceneGraph::Camera3D& camera) {
            _shader
                .setViewProjectionMatrix(camera.projectionMatrix()*transformation)
                .draw(_mesh);
        }

    private:
        PointShader& _shader;
        GL::Mesh& _mesh;
};

Viewer::Viewer(const Arguments& arguments, TreeDetector& detector):
    Platform::Application{
        arguments, 
        Configuration{}.setTitle("geo1015.hw03").setWindowFlags(Configuration::WindowFlag::Resizable)
    },
    _detector{detector}
{
    _imgui = ImGuiIntegration::Context(Vector2{windowSize()}/dpiScaling(),
        windowSize(), framebufferSize());

    /* OpenGL settings */
    GL::Renderer::setBlendEquation(GL::Renderer::BlendEquation::Add,
        GL::Renderer::BlendEquation::Add);
    GL::Renderer::setBlendFunction(GL::Renderer::BlendFunction::SourceAlpha,
        GL::Renderer::BlendFunction::OneMinusSourceAlpha);
    GL::Renderer::enable(GL::Renderer::Feature::DepthTest);
    GL::Renderer::enable(GL::Renderer::Feature::FaceCulling);
    GL::Renderer::enable(GL::Renderer::Feature::ProgramPointSize);

    setMinimalLoopPeriod(16);
    GL::Renderer::setClearColor(_clearColor);

    // data
    const auto& input_points = _detector.get_input_points();
    std::vector<float> data_points;
    data_points.reserve(input_points.size()*3);
    std::vector<int> data_labels;
    data_labels.reserve(input_points.size());


    BBox _data_box(input_points);
    double3 center = _data_box.center();
    for (const auto& p : input_points) {
        data_points.push_back(float(p.x-center.x));
        data_points.push_back(float(p.y-center.y));
        data_points.push_back(float(p.z-center.z));
        data_labels.push_back(p.segment_id);
        _segments[p.segment_id]++;
    }

    _vertexBuffer.setData(data_points);
    _labelBuffer.setData(data_labels);

    _mesh.setPrimitive(GL::MeshPrimitive::Points)
        .setCount(input_points.size())
        .addVertexBuffer(_vertexBuffer, 0, PointShader::Position{})
        .addVertexBuffer(_labelBuffer, 0, PointShader::Label{});

    // colormap
    randomiseColormap();
    auto image = ImageView1D{PixelFormat::RGB32F, CMAP_SIZE, _colormap};
    _texture.setWrapping(GL::SamplerWrapping::Repeat)
        .setMagnificationFilter(GL::SamplerFilter::Nearest)
        .setMinificationFilter(GL::SamplerFilter::Nearest)
        .setStorage(1, GL::textureFormat(image.format()), image.size())
        .setSubImage(0, {}, image);

    // drawables
    auto object = new Object3D{&_scene};
    new VisualizationDrawable{*object, _shader, _mesh, _drawables};

    /* Set up the camera */
    {
        /* Setup the arcball after the camera objects */
        const Vector3 eye = Vector3::zAxis(500.0f);
        const Vector3 center{};
        const Vector3 up = Vector3::yAxis();
        _arcballCamera.emplace(_scene, eye, center, up, 45.0_degf,
            windowSize(), framebufferSize());
    }
}

void Viewer::updateColormap() {
    _texture.setSubImage(0, {}, 
        ImageView1D{PixelFormat::RGB32F, CMAP_SIZE, _colormap}
    );
}

void Viewer::randomiseColormap() {
    std::random_device rd; // obtain a random number from hardware
    std::mt19937 gen(rd()); // seed the generator
    std::uniform_real_distribution<float> distr(0.0, 1.0);
    for (int i=0; i<(CMAP_SIZE*3); ++i) {
        _colormap[i] = distr(gen);
    }
    _colormap[0*3+0] = 1.0;
    _colormap[0*3+1] = 1.0;
    _colormap[0*3+2] = 1.0;
}

void Viewer::drawEvent() {
    GL::defaultFramebuffer.clear(GL::FramebufferClear::Color | GL::FramebufferClear::Depth);

    _imgui.newFrame();
    /* Enable text input, if needed */
    if(ImGui::GetIO().WantTextInput && !isTextInputActive())
        startTextInput();
    else if(!ImGui::GetIO().WantTextInput && isTextInputActive())
        stopTextInput();

    /* Drawing code */
    _shader
        .setPointSize(_pointSize)
        .bindTexture(_texture);
    _arcballCamera->update();
    _arcballCamera->draw(_drawables);

    /* ImGui */
    {
        ImGui::Begin("Settings & controls");
        ImGui::Text("Rotate view with mouse drag");
        ImGui::Text("Move with shift+mouse drag");
        ImGui::SliderFloat("Point size", &_pointSize, 1.0f, 5.0f);
        if(ImGui::ColorEdit3("Background", _clearColor.data())) {
            GL::Renderer::setClearColor(_clearColor);
        }
        if(ImGui::Button("Randomise segment colors")) {
            randomiseColormap();
            updateColormap();
        }
        ImGui::SameLine();
        if(ImGui::Button("Reset camera")) {
            _arcballCamera->reset();
        }
            
        ImGui::Separator();
        if(ImGui::CollapsingHeader("Segments")) {

            ImGui::Text("Total: %lu\nSegment <id> [<point count>]", _segments.size());
            ImGui::Text("Segment 0 are the unsegmented points!");
            for (auto& [seg_id, seg_count] : _segments){
                ImGui::PushID(seg_id);
                if(ImGui::ColorEdit3("col##3", &_colormap[(seg_id*3)%CMAP_SIZE], ImGuiColorEditFlags_NoInputs | ImGuiColorEditFlags_NoLabel)) {
                    updateColormap();
                }
                ImGui::SameLine();
                ImGui::Text("Segment %d [%d]", seg_id, seg_count);
                ImGui::PopID();
            }
        }
        ImGui::End();
        
        // ImGui::Text("Application average %.3f ms/frame (%.1f FPS)",
        //     1000.0/Double(ImGui::GetIO().Framerate), Double(ImGui::GetIO().Framerate));
    }

    /* Update application cursor */
    // _imgui.updateApplicationCursor(*this);

    /* Set appropriate states. If you only draw ImGui, it is sufficient to
       just enable blending and scissor test in the constructor. */
    GL::Renderer::enable(GL::Renderer::Feature::Blending);
    GL::Renderer::enable(GL::Renderer::Feature::ScissorTest);
    GL::Renderer::disable(GL::Renderer::Feature::FaceCulling);
    GL::Renderer::disable(GL::Renderer::Feature::DepthTest);

    _imgui.drawFrame();

    /* Reset state. Only needed if you want to draw something else with
       different state after. */
    GL::Renderer::enable(GL::Renderer::Feature::DepthTest);
    GL::Renderer::enable(GL::Renderer::Feature::FaceCulling);
    GL::Renderer::disable(GL::Renderer::Feature::ScissorTest);
    GL::Renderer::disable(GL::Renderer::Feature::Blending);

    swapBuffers();
    redraw();
}


void Viewer::viewportEvent(ViewportEvent& event) {
    GL::defaultFramebuffer.setViewport({{}, event.framebufferSize()});

    _imgui.relayout(Vector2{event.windowSize()}/event.dpiScaling(),
        event.windowSize(), event.framebufferSize());

    _arcballCamera->reshape(event.windowSize(), event.framebufferSize());
}

void Viewer::keyPressEvent(KeyEvent& event) {
    if(_imgui.handleKeyPressEvent(event)) return;

    switch(event.key()) {
        case KeyEvent::Key::L:
            if(_arcballCamera->lagging() > 0.0f) {
                Debug{} << "Lagging disabled";
                _arcballCamera->setLagging(0.0f);
            } else {
                Debug{} << "Lagging enabled";
                _arcballCamera->setLagging(0.85f);
            }
            break;
        case KeyEvent::Key::R:
            _arcballCamera->reset();
            break;

        default: return;
    }

    event.setAccepted();
    redraw();
}

void Viewer::keyReleaseEvent(KeyEvent& event) {
    if(_imgui.handleKeyReleaseEvent(event)) return;
}

void Viewer::mousePressEvent(MouseEvent& event) {
    if(_imgui.handleMousePressEvent(event)) return;

    _arcballCamera->initTransformation(event.position());

    event.setAccepted();
    redraw();
}

void Viewer::mouseReleaseEvent(MouseEvent& event) {
    if(_imgui.handleMouseReleaseEvent(event)) return;
}

void Viewer::mouseMoveEvent(MouseMoveEvent& event) {
    if(_imgui.handleMouseMoveEvent(event)) return;

    if(!event.buttons()) return;

    if(event.modifiers() & MouseMoveEvent::Modifier::Shift)
        _arcballCamera->translate(event.position());
    else _arcballCamera->rotate(event.position());

    event.setAccepted();
    redraw();
}

void Viewer::mouseScrollEvent(MouseScrollEvent& event) {
    if(_imgui.handleMouseScrollEvent(event)) {
        /* Prevent scrolling the page */
        event.setAccepted();
        return;
    }

    const Float delta = event.offset().y();
    if(Math::abs(delta) < 1.0e-2f) return;

    _arcballCamera->zoom(50*delta);

    event.setAccepted();
    redraw();
}

void Viewer::textInputEvent(TextInputEvent& event) {
    if(_imgui.handleTextInputEvent(event)) return;
}

int runViewer(TreeDetector& detector, int argc, char** argv) {
    Viewer app({argc, argv}, detector);
    return app.exec();
}
