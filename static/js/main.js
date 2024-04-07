// $(document).ready(function () {
//   const toggle = document.getElementById("toggleDark");
//   const body = document.querySelector("body");

//   toggle.addEventListener("click", function () {
//     this.classList.toggle("bi-moon");
//     if (this.classList.contains("bi-moon")) {
//       body.style.background = "black";
//       body.style.color = "white";
//       body.style.transition = "2s";
//     } else {
//       body.style.background = "white";
//       body.style.color = "black";
//       body.style.transition = "2s";
//     }
//   });
// });
$(function () {
  var dd1 = new dropDown($("#myDropdown"));

  $(document).click(function () {
    $(".wrapper-dropdown").removeClass("active");
  });

  $("#download-api").click(function () {
    var selected_api = $("#myDropdown span").data("selected-api");

    $.ajax({
      type: "POST",
      url: "/process_request",
      data: {
        mpesa: $("#mpesa-verified").val(),
        selected_api: selected_api,
      },
      success: function (response) {
        if (response.status === "success") {
          $(".alert").remove();

          var link = document.createElement("a");
          link.href =
            "data:text/json;charset=utf-8," +
            encodeURIComponent(JSON.stringify(response.data));
          link.download = "api_key.json";
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          console.log("API key downloaded successfully");
          alertSuccess("API key downloaded successfully");
          document.querySelector(".popup-download").classList.remove("active");
        } else {
          $(".alert").remove();

          alertError(response.message);
          if (response.message === "Please verify your M-Pesa receipt") {
            alertError("Please verify your M-Pesa receipt");
          } else if (response.message === "API key not found") {
            alertError("API key not found");
          } else if (response.message === "No API key selected") {
            alertError("No API key selected");
          } else if (
            response.message === "Mpesa receipt number does not exist"
          ) {
            alertError("Mpesa receipt number does not exist");
          }
        }
      },
      error: function () {
        // Remove any existing alerts
        $(".alert").remove();

        alertError("Error occurred while processing request");
      },
    });
  });
});

function dropDown(el) {
  this.dd = el;
  this.placeholder = this.dd.children("span");
  this.opts = this.dd.find("ul.dropdown > li");
  this.val = "";
  this.index = -1;
  this.initEvents();
}

dropDown.prototype = {
  initEvents: function () {
    var obj = this;

    obj.dd.on("click", function () {
      $(this).toggleClass("active");
      return false;
    });

    obj.opts.on("click", function () {
      var opt = $(this);
      obj.val = opt.text();
      obj.index = opt.index();
      obj.placeholder.text(obj.val);
      obj.placeholder.data("selected-api", obj.val);
      obj.printSelected();
    });
  },

  printSelected: function () {
    console.log("Selected: " + this.val);
  },
};

document.querySelector("#show-pay").addEventListener("click", function () {
  document.querySelector(".popup").classList.add("active");
});
document.querySelector("#show-verify").addEventListener("click", function () {
  document.querySelector(".popup-verify").classList.add("active");
});
document.querySelector("#show-download").addEventListener("click", function () {
  document.querySelector(".popup-download").classList.add("active");
});
document
  .querySelector(".popup .close-btn")
  .addEventListener("click", function () {
    document.querySelector(".popup").classList.remove("active");
  });
document
  .querySelector(".popup-verify .close-btn")
  .addEventListener("click", function () {
    document.querySelector(".popup-verify").classList.remove("active");
  });
document
  .querySelector(".popup-download .close-btn")
  .addEventListener("click", function () {
    document.querySelector(".popup-download").classList.remove("active");
  });
document.getElementById("sendRequest").addEventListener("click", function () {
  var phoneNumber = document.getElementById("phone").value;

  if (!phoneNumber.trim()) {
    alertError("Please enter a phone number: 254XXXXXXXXX");
    return;
  }

  if (!isValidPhoneNumber(phoneNumber)) {
    alertError("Please enter a valid phone number in the format 2547XXXXXXXX");
    return;
  }

  sendRequestToServer(phoneNumber);
});

function isValidPhoneNumber(phoneNumber) {
  var phoneRegex = /^254\d{9}$/;
  return phoneRegex.test(phoneNumber);
}

function alertSuccess(message) {
  $(".alert-success").remove();

  var alertDiv = $(
    '<div class="alert alert-success alert-dismissible fade show" role="alert">' +
      "<strong>Success!</strong> " +
      message +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span>' +
      "</button>" +
      "</div>"
  );

  $("#alerts").append(alertDiv);

  setTimeout(function () {
    setTimeout(function () {
      alertDiv.alert("close");
    }, 3000);
  }, 100);
}

function alertError(message) {
  $(".alert-danger").remove();

  var alertDiv = $(
    '<div class="alert alert-danger alert-dismissible fade show" role="alert">' +
      "<strong>Error!</strong> " +
      message +
      '<button type="button" class="close" data-dismiss="alert" aria-label="Close">' +
      '<span aria-hidden="true">&times;</span>' +
      "</button>" +
      "</div>"
  );

  $("#alerts").append(alertDiv);

  setTimeout(function () {
    setTimeout(function () {
      alertDiv.alert("close");
    }, 3000);
  }, 100);
}

function sendRequestToServer(phoneNumber) {
  var xhr = new XMLHttpRequest();
  var url = "/initiate";
  var data = JSON.stringify({ phone: phoneNumber });

  xhr.open("POST", url, true);
  xhr.setRequestHeader("Content-Type", "application/json");
  xhr.onreadystatechange = function () {
    if (xhr.readyState === 4 && xhr.status === 200) {
      var response = JSON.parse(xhr.responseText);
      console.log(response);
      alertSuccess("STK Kit initiated successfully");
      document.querySelector(".popup").classList.remove("active");
    } else if (xhr.readyState === 4) {
      console.error(xhr.responseText);
      alert("Error: " + xhr.responseText);
    }
  };
  xhr.send(data);
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("verify").addEventListener("click", function () {
    var mpesaReceiptNumber = document
      .getElementById("mpesa")
      .value.trim()
      .toUpperCase();

    if (!mpesaReceiptNumber) {
      alertError("Please enter a M-Pesa receipt number.");
      return;
    }

    if (mpesaReceiptNumber.length !== 10) {
      alertError("Please enter a 10-character long M-Pesa receipt number.");
      return;
    }

    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/verify", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
      if (xhr.readyState === XMLHttpRequest.DONE) {
        if (xhr.status === 200) {
          var response = JSON.parse(xhr.responseText);

          if (
            response.message === "M-Pesa receipt number verified successfully"
          ) {
            console.log("Response message:", response.message);
            alertSuccess(response.message);
            document.querySelector(".popup-verify").classList.remove("active");
          } else if (
            response.message === "M-Pesa receipt number already verified"
          ) {
            alertError(response.message);
          } else {
            alertError(response.message);
          }
        } else {
          var errorMessage = xhr.responseText
            .split(": ")[1]
            .replace(/"/g, "")
            .replace(/}/g, "");
          alertError(errorMessage);
        }
      }
    };
    xhr.send(JSON.stringify({ mpesa_receipt_number: mpesaReceiptNumber }));
  });
});
