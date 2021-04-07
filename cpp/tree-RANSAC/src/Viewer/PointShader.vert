uniform highp mat4 viewProjectionMatrix;
uniform float pointSize;

layout(location = 0) in vec3 position;
layout(location = 1) in int label;

flat out int pixelLabel;

void main() {
    pixelLabel = label;

    gl_PointSize = pointSize;
    gl_Position = mat4(viewProjectionMatrix) * vec4(position, 1.0);
}