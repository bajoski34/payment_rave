/* global Rave */
odoo.define("payment_rave.payment_form", (require) => {
  "use strict";

  const core = require("web.core");
  const checkoutForm = require("payment.checkout_form");
  const manageForm = require("payment.manage_form");

  const ajax = require("web.ajax");
  const _t = core._t;
  const qweb = core.qweb;
  ajax.loadXML("/payment_rave/static/src/xml/rave_templates.xml", qweb);

  if ($.blockUI) {
    // our message needs to appear above the modal dialog
    $.blockUI.defaults.baseZ = 2147483647; //same z-index as Rave Checkout
    $.blockUI.defaults.css.border = "0";
    $.blockUI.defaults.css["background-color"] = "";
    $.blockUI.defaults.overlayCSS["opacity"] = "0.9";
  }

  const raveMixin = {
    /**
     * Redirect the customer to Stripe hosted payment page.
     *
     * @override method from payment.payment_form_mixin
     * @private
     * @param {string} provider - The provider of the payment option's acquirer
     * @param {number} paymentOptionId - The id of the payment option handling the transaction
     * @param {object} processingValues - The processing values of the transaction
     * @return {undefined}
     */
    _processRedirectPayment: function (
      provider,
      paymentOptionId,
      processingValues
    ) {
      if (provider !== "rave") {
        return this._super(...arguments);
      }

      console.log("rave payment");
      console.log(provider, paymentOptionId, processingValues); //
      console.log("rave payment");

      this._payWithRave(processingValues);
    },

    _payWithRave: function (processingValues) {
      const {
        tx_ref,
        public_key,
        redirect_url,
        amount,
        currency,
        email,
        firstname,
        lastname,
      } = processingValues;
      var x = FlutterwaveCheckout({
        public_key: public_key,
        tx_ref: tx_ref,
        amount: amount,
        currency: currency,
        customer: {
          email: email,
          phone_number: "-",
          name: firstname + " " + lastname,
        },
        onclose: function () {},
        callback: function (data) {
          const { amount, currency, customer, status, tx_ref } = data;
          // collect tx_ref returned and pass to a server page to complete status check.
          if ($.blockUI) {
            var msg = _t("Just one more second, confirming your payment...");
            $.blockUI({
              message:
                '<h2 class="text-white"><img src="/web/static/src/img/spin.png" class="fa-pulse"/>' +
                "    <br />" +
                msg +
                "</h2>",
            });
          }
          if (
            (status === "successful" && tx_ref !== undefined) ||
            tx_ref !== null
          ) {
            // redirect to a success page
            ajax
              .jsonRpc("/payment/rave/verify_charge", "call", {
                data: data,
                tx_ref: tx_ref,
              })
              .then(function (data) {
                window.location.href = data;
              })
              .catch(function (data) {
                var msg = data && data.data && data.data.message;
                var wizard = $(
                  qweb.render("rave.error", {
                    msg: msg || _t("Payment error"),
                  })
                );
                wizard.appendTo($("body")).modal({
                  keyboard: true,
                });
              });
          } else {
            console.log("Failed here!");
            var wizard = $(
              qweb.render("rave.error", {
                msg: msg || _t("Payment error"),
              })
            );
            wizard.appendTo($("body")).modal({
              keyboard: true,
            });
          }

          x.close(); // use this to close the modal immediately after payment.
        },
        customizations: {
          title: "Sample Test",
          description: "Payment for items in cart",
          logo: "https://assets.piedpiper.com/logo.png",
        },
      });
    },
  };

  require("web.dom_ready");
  if (!$(".o_payment_form").length) {
    return $.Deferred().reject("DOM doesn't contain '.o_payment_form'");
  } else {
    function display_rave_form(provider_form) {
      // Open Checkout with further options
      var payment_form = $(".o_payment_form");
      if (!payment_form.find("i").length)
        payment_form.append('<i class="fa fa-spinner fa-spin"/>');
      payment_form.attr("disabled", "disabled");

      var payment_tx_url = payment_form
        .find('input[name="prepare_tx_url"]')
        .val();
      var access_token =
        $("input[name='access_token']").val() ||
        $("input[name='token']").val() ||
        "";

      var get_input_value = function (name) {
        return provider_form.find('input[name="' + name + '"]').val();
      };

      ajax
        .jsonRpc("/payment/values", "call", {
          acquirer_id: parseInt(provider_form.find("#acquirer_rave").val()),
          amount: parseFloat(get_input_value("amount") || "0.0"),
          currency: get_input_value("currency"),
          email: get_input_value("email"),
          name: get_input_value("name"),
          publicKey: get_input_value("rave_pub_key"),
          invoice_num: get_input_value("invoice_num"),
          phone: get_input_value("phone"),
          return_url: get_input_value("return_url"),
          merchant: get_input_value("merchant"),
        })
        .then(function (data) {
          payWithRave(
            data.publicKey,
            data.email,
            data.amount,
            data.phone,
            data.currency,
            data.invoice_num,
            data.name
          );
        })
        .catch(function (data) {
          console.log("Failed!");
          var msg = data && data.data && data.data.message;
          var wizard = $(
            qweb.render("rave.error", {
              msg: msg || _t("Payment error"),
            })
          );
          wizard.appendTo($("body")).modal({
            keyboard: true,
          });
        });
    }

    var environment = $("input[name='environment']").val();

    if (environment === "prod") {
      var url =
        "https://api.ravepay.co/flwv3-pug/getpaidx/api/flwpbf-inline.js";
    } else {
      var url =
        "https://api.ravepay.co/flwv3-pug/getpaidx/api/flwpbf-inline.js";
    }

    $.getScript(url, function (data, textStatus, jqxhr) {
      display_rave_form($('form[provider="rave"]'));
    });
  }

  checkoutForm.include(raveMixin);
  manageForm.include(raveMixin);
});
