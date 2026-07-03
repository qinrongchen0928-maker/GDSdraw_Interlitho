from __future__ import annotations

from datetime import datetime

import streamlit as st

from gds_generators import generate_1d_grating, generate_2d_periodic, generate_from_image
from gds_generators.image_to_gds import image_bytes_to_mask
from gds_generators.preview import (
    mask_overview,
    periodic_detail_1d,
    periodic_detail_2d,
    periodic_overview_1d,
    periodic_overview_2d,
)


st.set_page_config(
    page_title="GDSdraw",
    page_icon="G",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def show_summary(summary: dict) -> None:
    st.caption("生成摘要")
    st.dataframe(
        [{"项目": key, "数值": value} for key, value in summary.items()],
        hide_index=True,
        use_container_width=True,
    )


def download_gds(data: bytes, filename: str) -> None:
    st.download_button(
        "下载 GDS",
        data=data,
        file_name=filename,
        mime="application/octet-stream",
        use_container_width=True,
    )


def show_periodic_previews(overview: bytes, detail: bytes) -> None:
    st.subheader("预览")
    st.caption("总面积尺度概览图")
    st.image(overview, use_container_width=True)
    st.caption("3 个周期尺度细节图")
    st.image(detail, use_container_width=True)


def periodic_page() -> None:
    structure_mode = st.segmented_control(
        "结构类型",
        ["一维光栅", "二维结构"],
        default="一维光栅",
    )

    layer = st.number_input("Layer", min_value=0, max_value=255, value=0, step=1)

    if structure_mode == "一维光栅":
        period = st.number_input("周期，单位 um", min_value=0.0001, value=3.2, step=0.1, format="%.4f")
        duty = st.slider("一维占空比", min_value=0.01, max_value=0.99, value=0.50, step=0.01)
        total_length = st.number_input("总长度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")
        total_width = st.number_input("总宽度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")

        if st.button("生成一维光栅 GDS", type="primary", use_container_width=True):
            try:
                result = generate_1d_grating(
                    period_um=period,
                    duty_cycle=duty,
                    total_length_um=total_length,
                    total_width_um=total_width,
                    layer=layer,
                    filename=f"gdsdraw_1d_grating_{timestamp()}.gds",
                )
                overview = periodic_overview_1d(period, duty, total_length, total_width)
                detail = periodic_detail_1d(period, duty, total_width)
                st.success("已生成。周期性复制使用 GDS 阵列引用。")
                show_periodic_previews(overview, detail)
                show_summary(result.summary)
                download_gds(result.data, result.filename)
            except Exception as exc:
                st.error(str(exc))

    else:
        shape_cn = st.selectbox("结构选择", ["圆形", "正方形", "矩形"])
        shape_map = {"圆形": "circle", "正方形": "square", "矩形": "rectangle"}
        shape = shape_map[shape_cn]

        diameter = square_side = rect_length = rect_width = None
        if shape == "circle":
            diameter = st.number_input("直径，单位 um", min_value=0.0001, value=1.0, step=0.1, format="%.4f")
            circle_points = st.slider("圆形近似点数", min_value=16, max_value=256, value=96, step=8)
        elif shape == "square":
            square_side = st.number_input("边长，单位 um", min_value=0.0001, value=1.0, step=0.1, format="%.4f")
            circle_points = 96
        else:
            rect_length = st.number_input("矩形长，单位 um", min_value=0.0001, value=1.0, step=0.1, format="%.4f")
            rect_width = st.number_input("矩形宽，单位 um", min_value=0.0001, value=0.5, step=0.1, format="%.4f")
            circle_points = 96

        period_x = st.number_input("X 周期，单位 um", min_value=0.0001, value=3.2, step=0.1, format="%.4f")
        period_y = st.number_input("Y 周期，单位 um", min_value=0.0001, value=3.2, step=0.1, format="%.4f")
        total_length = st.number_input("总长度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")
        total_width = st.number_input("总宽度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")

        if st.button("生成二维结构 GDS", type="primary", use_container_width=True):
            try:
                result = generate_2d_periodic(
                    shape=shape,
                    period_x_um=period_x,
                    period_y_um=period_y,
                    total_length_um=total_length,
                    total_width_um=total_width,
                    diameter_um=diameter,
                    square_side_um=square_side,
                    rectangle_length_um=rect_length,
                    rectangle_width_um=rect_width,
                    circle_points=circle_points,
                    layer=layer,
                    filename=f"gdsdraw_2d_{shape}_{timestamp()}.gds",
                )
                overview = periodic_overview_2d(
                    shape,
                    period_x,
                    period_y,
                    total_length,
                    total_width,
                    diameter=diameter,
                    square_side=square_side,
                    rect_l=rect_length,
                    rect_w=rect_width,
                )
                detail = periodic_detail_2d(
                    shape,
                    period_x,
                    period_y,
                    diameter=diameter,
                    square_side=square_side,
                    rect_l=rect_length,
                    rect_w=rect_width,
                )
                st.success("已生成。周期性复制使用 GDS 阵列引用。")
                show_periodic_previews(overview, detail)
                show_summary(result.summary)
                download_gds(result.data, result.filename)
            except Exception as exc:
                st.error(str(exc))


def image_page() -> None:
    uploaded = st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "bmp", "tif", "tiff"])
    actual_length = st.number_input("图片实际长度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")
    actual_width = st.number_input("图片实际宽度，单位 um", min_value=0.0001, value=1000.0, step=100.0, format="%.4f")
    threshold = st.slider("二值化阈值", min_value=0, max_value=255, value=128, step=1)
    invert = st.toggle("反转黑白对应关系", value=False)
    layer = st.number_input("Layer", min_value=0, max_value=255, value=0, step=1)
    max_pixels = st.number_input("最大处理像素数", min_value=10000, value=2_000_000, step=10000)

    if uploaded is not None:
        st.caption(f"文件大小：{uploaded.size / 1024 / 1024:.2f} MB")

    if st.button("根据图片生成 GDS", type="primary", use_container_width=True):
        if uploaded is None:
            st.error("请先上传图片。")
            return

        try:
            image_bytes = uploaded.getvalue()
            result = generate_from_image(
                image_bytes=image_bytes,
                actual_length_um=actual_length,
                actual_width_um=actual_width,
                threshold=threshold,
                invert=invert,
                layer=layer,
                max_pixels=int(max_pixels),
                filename=f"gdsdraw_image_{timestamp()}.gds",
            )
            mask = image_bytes_to_mask(image_bytes, threshold=threshold, invert=invert)
            st.success("已生成。图片结构区域已按行合并为矩形，减少 GDS 图元数量。")
            st.subheader("预览")
            st.caption("总面积尺度概览图")
            st.image(mask_overview(mask), use_container_width=True)
            show_summary(result.summary)
            download_gds(result.data, result.filename)
        except Exception as exc:
            st.error(str(exc))


st.title("GDSdraw")
st.caption("输入参数或上传图片，生成可下载的 GDS 文件。")

mode = st.radio(
    "生成方式",
    ["参数生成周期性结构", "根据图片生成 GDS"],
    horizontal=True,
)

if mode == "参数生成周期性结构":
    periodic_page()
else:
    image_page()
