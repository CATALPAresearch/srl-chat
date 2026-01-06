<template>
    <div class="col-12 col-md-10 col-lg-8">
       <!-- 
            v-show="$store.getters.getInformedConsentAgreement != 'yes' && $store.getters.getInformedConsentAgreement != 'no'"
        -->
        <div
            v-show="$store.getters.getInformedConsentAgreement == 'none'"
            v-cloak 
            class="mb-3 alert alert-primary" role="dialog">
            <h5>Diese Anwendung ist Teil der KI-Experimentierumgebung und erfordert Ihre Einwilligung.</h5>
            <button @click="$store.commit('setInformedConsentAgreement', 'no')"
                class="btn btn-primary btn-block">Einwilligungserklärung jetzt anzeigen</button>
        </div>
        <div v-if="$store.getters.getInformedConsentAgreement == 'no'" class="alert alert-info" role="dialog">
            <h5>Einwilligung in die Nutzung von OpenChat</h5>
            <h4>Zweck der Untersuchung in OpenChat</h4>
            <p class="lead text-wrap">Die Untersuchung in OpenChat dient dazu die technischen und didaktischen
                Voraussetzungen für die Anwendung
                von Large Language Models (LLMs) für das Lernen und Lehren zu ermitteln und herzustellen.</p>
            <h4>Erfasste und verarbeitete Daten</h4>
            <p class="lead text-wrap">
                Während der Nutzung von OpenChat werden Interaktionen wie Klicks, Texteingaben und die für den
                Dokument-Chat
                bereitgestellten Dokumente (bspw. PDFs, Moodle-Ressourcen) sowie die Antworten der Sprachmodelle in
                pseudonymisierter Form erfasst.
                Bitte laden Sie keine Dokumente hoch, die personenbezogene Daten Dritter enthalten. Machen Sie keine
                Eingaben,
                die personenbezogene Daten Dritter enthalten.
                Nach der Erfassung und Speicherung dieser Daten ist eine Zuordnung von Pseudonym und Nutzenden oder
                Moodle
                Nutzer-ID nicht mehr möglich.</p>
            <h4>Verwendung der Daten</h4>
            <p class="lead text-wrap">
                Die erfassten Daten werden verwendet, um den technischen Betrieb und Benutzerfreundlichkeit von OpenChat
                und
                den verbundenen Diensten (bspw. RAG-Webservice, FLEXI LLM-Server) zu überwachen, zu analysieren und zu
                verbessern.
                Selbige Daten werden auch genutzt und wissenschaftliche Fragestellungen zur Nutzung und Qualität von
                Lehrangeboten im Zusammenhang mit Sprachmodellen zu beantworten.
                Die Verarbeitung erfolgt auf Grundlage Ihrer freiwilligen Einwilligung (Art. 6 Abs. 1 lit. a DSGVO).
                Ihre Einwilligung kann jederzeit mit Wirkung für die Zukunft widerrufen werden.

                Die Verarbeitung erfolgt ausschließlich auf Servern der FernUniversität im Einklang mit den geltenden
                Datenschutzbestimmungen.
            </p>
            <h4>Rechte</h4>
            <p class="lead text-wrap">
                Nutzenden Studierenden und Lehrende sind nicht verpflichtet OpenChat zu nutzen. Die Einwilligung in die
                Erfassung und Verarbeitung der oben genannten Daten erfolgt freiwillig durch eine Zustimmung (opt-in).
                Die
                Einwilligung kann jeder Zeit widerrufen werden.
                Lehrende könne OpenChat freiwillig im Rahmen eines Moodle-Kurses einsetzen und den Kursteilnehmenden
                anbieten.
                Durch Löschung der OpenChat-Aktivität aus dem Kurs kann die Nutzung durch Studierende jeder Zeit
                unterbunden
                werden.
                Daten von Nutzenden können weder herausgegeben, noch gelöscht werden, da die Daten pseudonym erfasst
                werden
                und ein Bezug zu einer Person nicht herstellbar ist.
            </p>
            <h4>Verantwortlichkeiten</h4>
            <p class="lead text-wrap">
                Verantwortlich für die Datenverarbeitung ist die FernUniversität in Hagen, Universitätsstraße 11, 58097
                Hagen.
                Bei Fragen wenden Sie sich bitte an den <a
                    href="mailto:datenschutzbeauftragter@fernuni-hagen.de">Behördlichen Datenschutzbeauftragten</a>.
                Technische Fragen beantworten Ihnen <a href="mailto:niels.seidel@fernuni-hagen.de">Dr. Niels Seidel</a>
                und <a href="mailto:torsten.zesch@fernuni-hagen">Prof. Dr. Torsten
                    Zesch</a>.
            </p>
            <hr>
            <div class="d-flex flex-column flex-md-row justify-content-between align-items-stretch mb-3">
                <button type="button" @click="$store.commit('setInformedConsentAgreement', 'yes')"
                    class="btn btn-primary mb-2 mb-md-0 mr-md-3 w-100 w-md-auto" aria-label="Einwilligung erteilen">
                    Ja, ich erteile die Einwilligung zur Erhebung und Verarbeitung meiner Daten in OpenChat!
                </button>
                <button type="button" @click="$store.commit('setInformedConsentAgreement', 'none')"
                    class="btn btn-outline-secondary w-100 w-md-auto" aria-label="Einwilligung nicht erteilen">
                    Nein, ich willige nicht ein.
                </button>
            </div>
        </div>
    </div>
</template>

<style scoped>

[v-cloak] .v-cloak--hidden{
  display: none !important;
}

[v-cloak] {
  display: none !important;
}

</style>