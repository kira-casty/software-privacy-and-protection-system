var swiper = new Swiper(".llm-slider", {
  spaceBetween: 30,
  effect: "fade",
  loop: true,
  mousewheel: {
    invert: false,
  },
  pagination: {
    el: ".llm-slider__pagination",
    clickable: true,
  },
});
document.querySelector("#show-verify").addEventListener("click", function () {
  document.querySelector(".popup-verify").classList.add("active");
});
document
  .querySelector(".popup-verify .close-btn")
  .addEventListener("click", function () {
    document.querySelector(".popup-verify").classList.remove("active");
  });
