
#include <Magnum/GL/AbstractShaderProgram.h>
#include <Magnum/GL/Texture.h>
#include <Magnum/Math/Matrix4.h>

using namespace Magnum;

class PointShader: public GL::AbstractShaderProgram {
    public:
        typedef GL::Attribute<0, Vector3> Position;
        typedef GL::Attribute<1, Int> Label;

        explicit PointShader();

        PointShader& setPointSize(Float size) {
            setUniform(_uPointSize, size);
            return *this;
        }

        PointShader& setViewProjectionMatrix(const Matrix4& matrix) {
            setUniform(_uViewProjectionMatrix, matrix);
            return *this;
        }

        PointShader& bindTexture(GL::Texture1D& texture) {
            texture.bind(TextureUnit);
            return *this;
        }

    private:
        enum: Int { TextureUnit = 0 };

        Int _uPointSize,
            _uViewProjectionMatrix;
};