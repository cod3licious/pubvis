<script setup lang="ts"></script>

<template>
    <main>
        <div id="about-text">
            <p>
                PubVis is a WebApp meant to help scientists with their literature research. Instead of having to search for a specific topic, the landscape of
                published research can be explored visually and papers similar in content to an article of interest are just a click away.
            </p>

            <p>
                With several thousands of papers published every year in the field of cancer research alone, it is too easy to miss an important finding
                relevant to one's own research. For example while you're uncovering the mechanisms linking a specific protein to pancreatic cancer, someone
                doing research on kidney cancer might have looked at the same protein in a different context already. But because of the magnitude of the field,
                if both of you are buried deep in your research, it might be a while before the two pieces of the puzzle get connected.
            </p>

            <p>
                While the references given in a paper are a starting point for digging deeper into a topic, authors can only cite what they know. This is why
                PubVis compares the actual texts of the published articles to one another to check their similarity, thereby encouraging interdisciplinary
                discoveries. Using a machine learning algorithm, this complex construct of similarities between all the papers in our database is then embedded
                in a colorful 2D map, ready to be used for getting an overview of the collected literature. For a paper of interest, similar articles are then
                listed to its side in more detail for fast access to relevant related research.
            </p>

            <p>
                Please understand that this is only a prototype, developed by <a href="https://franziskahorn.de/" target="_blank">Dr. Franziska Horn</a> with
                the help of <a href="https://www.linkedin.com/in/marcel-lengert/" target="_blank">Marcel Lengert</a>. More details on the implementation can be
                found in the corresponding <a href="http://arxiv.org/abs/1706.08094" target="_blank">paper</a> or directly in the
                <a href="https://github.com/cod3licious/pubvis/" target="_blank">code</a>. Feedback is very much appreciated and can be directed to
                cod3licious[at]gmail[dot]com. Enjoy!
            </p>
        </div>
    </main>
</template>

<style scoped lang="scss">
#about-text {
    padding: 3em;
}
</style>
