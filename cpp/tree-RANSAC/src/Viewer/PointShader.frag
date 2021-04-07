uniform sampler1D textureData;

flat in int pixelLabel;

out vec4 fragmentColor;

void main() {
    fragmentColor.rgb = texture(textureData, float(pixelLabel)/512).rgb;
    fragmentColor.a = 1.0;
}